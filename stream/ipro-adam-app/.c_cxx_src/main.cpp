/*!
 @addtogroup  Adam Application
 @{
 @file        main.cpp
 @brief       Module to call Python Script in AdamApp Python Version
 @author      Panasonic
 @date        2020-06-17
 @version     1.0
 @par Copyright
 (C) COPYRIGHT 2020 Panasonic Corporation
 (C) COPYRIGHT 2022 i-PRO Co., Ltd.
*/

/******************************************************************************
 * Include header files
 ******************************************************************************/
/** Standard header files used in this application */
/** サンプルのアプリが使用するヘッダ               */
#include <Python.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>


#include <string>
#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <chrono>

/** ADAM header files used in this application           */
/** 追加アプリとして必ず必要な機能を組み込むためのヘッダ */
#include "AdamApi.h"

/** ADAM header files for debug printf */
#define ADAM_APP_DEBUG_ENABLE 1
#include "AdamDebug.h"

/**
 *  Eanble this macro,
 *  in case that the stdout and stderr streams in python is unbuffered.
 */
#define PYTHON_STDOUT_IS_UNBUFFERED

/******************************************************************************
 *  Static variables
 ******************************************************************************/
static E_ADAM_STOP_FACTOR s_stopFactor = ADAM_STOP_FACTOR_MAX;
static T_ADAM_EVENTLOOP_ID s_systemEventloopId = ADAM_INVALID_EVENTLOOP_ID;
static PyObject* s_pAdamModule = NULL;
static std::mutex s_mtx;
static std::condition_variable s_cndForPyThd;
static PyThreadState *_save;

/******************************************************************************
 *  Static functions
 ******************************************************************************/
static void pyThread();
static void initPython();
static void executePython();
static void finalizePython();

/** Handler for application STOP request from adamCore process */
static void stop_handler( E_ADAM_STOP_FACTOR factor );

/** Handler for sending application data request from the host ( via adamCore ) */
static void server_request_receive_handler( T_ADAM_REQUEST_ID requestId, ST_ADAM_NET_DATA* pData );
static void sendHttpResponse(T_ADAM_REQUEST_ID reqId, PyObject* pArg);
static void appPref_handler(char* const pPrefName[], const unsigned int prefSize);


class PyGILStateLock
{
public:
	PyGILStateLock(){
		m_gstate = PyGILState_Ensure();
	};
	~PyGILStateLock(){ PyGILState_Release(m_gstate); };

private:
	PyGILState_STATE m_gstate;
};

/******************************************************************************
 *  Functions
 ******************************************************************************/

/**
 * @brief main function
 *        メイン関数
 * @param argc   [in] int		count of arguments
 * @param argv[] [in] char*		arguments
 * @return            int	0	normal response
 * @return            int	-1	abnormal response
 */
int
main( int argc, char* argv[] )
{
	//setenv("PYTHONHOME", "/mnt/system/", 1);
	setenv("PYTHONHOME", "/", 1);
	setenv("PYTHONDONTWRITEBYTECODE", "1", 0); // pycache無効化

	ADAM_DEBUG_SET_PRINT_LEVELS(ADAM_LV_FTL | ADAM_LV_CRI | ADAM_LV_ERR | ADAM_LV_INF);
	//ADAM_DEBUG_SET_PRINT_LEVELS(0xffffffff);
	ADAM_DEBUG_SET_PRINT_MSEC(true);

	E_ADAM_ERR			err;		/** ADAM error code */
	ST_ADAM_SYSTEM_HANDLERS		handlers;	/** Handlers required by ADAM system */
	E_ADAM_START_FACTOR		startFactor;	/** Start factor(not defined) */
	int retFunc = -1;

	/**
	 *  Start to use ADAM library
	 *  ADAMライブラリの使用開始
	 *   Create the system event loop and set systemEventloopId
	 *   同時にイベントループも生成され、systemEventloopIdが返される
	 *   Arg 1 is the coding model about this application
	 *   第一引数ではアプリのコーディングモデルを指定する。
	 *   - ADAM_APP_TYPE_SKELETON   : Create only the main thread and use worker threads
	 *                                メインスレッドとWorkerスレッドのみで全ての処理を行うモデル。
	 *   - ADAM_APP_TYPE_FREE_STYLE : User can freely make threads for this application
	 *                                自由にスレッドを起こして処理を行うモデル。
	 *
	 *   === This sample program is using the model of Freestyle. ===
	 *   === このアプリはFreestyleモデルとして動作します ===
	 */
	handlers.m_stopHandler                 = stop_handler;
	handlers.m_serverRequestReceiveHandler = server_request_receive_handler;
	handlers.m_notifyAppPrefUpdateHandler  = appPref_handler;

	err = ADAM_Open( ADAM_APP_TYPE_SKELETON, &handlers, &s_systemEventloopId, &startFactor );
	if ( ADAM_ERR_OK != err ) {
		return retFunc;
	}

	setvbuf(stdout, NULL, _IONBF, 0);
	//dup3(fileno(g_pDebugPrintFd), fileno(stdout), O_CLOEXEC);

	initPython();

	std::thread thd(pyThread);
	thd.detach();

	Py_UNBLOCK_THREADS
	ADAM_Eventloop_Dispatch(s_systemEventloopId);

	if( s_stopFactor != ADAM_STOP_FACTOR_APPLICATION ){
		std::unique_lock<std::mutex> lk(s_mtx);
		s_cndForPyThd.wait_for(lk, std::chrono::seconds(10));

	}
	Py_BLOCK_THREADS

	finalizePython();

	/** Close ADAM (Exit this application process.) */
	ADAM_DEBUG_PRINT(ADAM_LV_INF, "ADAM_Close()!");
	ADAM_Close();

	return 0;
}

void pyThread()
{
	executePython();

	if( s_stopFactor == ADAM_STOP_FACTOR_MAX ){
		ADAM_StopMe();
	}
	s_cndForPyThd.notify_one();
	return;
}


void initPython()
{
	/** Pythonのサーチパス追加 */
#if defined(ADAM_TARGET_PF_ipro_ambaCV5XCAZ_linux) || defined( ADAM_TARGET_PF_ipro_ambaCV5XCEX_linux )
	// コンテナ版はpythonの設定パスが変更になる。
	std::string pythonPath = std::string("/app/python");
#else
	std::string pythonPath = std::string(ADAM_GetAppDataDirPath()) + "/../python";
#endif
	std::string pythonSitePkgPath = pythonPath + "/site-packages";
	pythonPath += ":";
	pythonPath += pythonSitePkgPath;
#if defined(ADAM_TARGET_PF_ipro_ambaCV5XCAZ_linux) || defined( ADAM_TARGET_PF_ipro_ambaCV5XCEX_linux )
	pythonPath += ":/lib:/usr/share/lib";
#else
	pythonPath += ":/lib";
#endif
#if 0
	std::string pythonDistPkgPath = pythonPath + "/dist-packages";
	pythonPath += ":";
	pythonPath += pythonDistPkgPath;
#endif
	if( getenv("PYTHONPATH") != NULL ){
		pythonPath += ":";
		pythonPath += getenv("PYTHONPATH");
	}
	setenv("PYTHONPATH", pythonPath.c_str(), 1);
	ADAM_DEBUG_PRINT(ADAM_LV_INF, "PYTHONPATH=%s\n", getenv("PYTHONPATH"));

#if defined(PYTHON_STDOUT_IS_UNBUFFERED)
	setenv("PYTHONUNBUFFERED", "false", 1);
#endif

	/** Python 初期化 */
	Py_Initialize();
	Py_DECREF(PyImport_ImportModule("threading"));
	PyEval_InitThreads();
#if 1
	/* adamモジュールインポート */
	s_pAdamModule = PyImport_ImportModule("libAdamApiPython");
	if( s_pAdamModule == NULL ){
		PyErr_Print();
		ADAM_DEBUG_PRINT(ADAM_LV_ERR, "PyImport_ImportModule Err\n");
	}
#endif
	return;
}

void executePython()
{
	std::string pyMain = "pymain.py";
#if defined(ADAM_TARGET_PF_ipro_ambaCV5XCAZ_linux) || defined( ADAM_TARGET_PF_ipro_ambaCV5XCEX_linux )
	std::string pyFile = std::string("/app/python/") + pyMain;
#else
	std::string pyFile = std::string(ADAM_GetAppDataDirPath()) + "/../python/" + pyMain;
#endif

	ADAM_DEBUG_PRINT( ADAM_LV_INF, "Python File = %s\n", pyMain.c_str() );
	ADAM_DEBUG_SET_PRINT_LEVELS(ADAM_LV_FTL | ADAM_LV_CRI | ADAM_LV_ERR);
	printf("************************* Start Python *************************\n");

	FILE* pFp = fopen(pyFile.c_str(), "r");

	//char dateTime[256];
	//getCurrentDateTime(dateTime, sizeof(dateTime), true, true);
	//printf("%s************************* Start Python *************************\n", dateTime);
	//std::cout << "aaaaaaaaaaaa2" <<std::endl << std::flush ;
	{
		PyGILStateLock _lock;
		int ret = PyRun_SimpleFile(pFp, pyFile.c_str());
		if( ret != 0 ){
			PyErr_Print();
			ADAM_DEBUG_PRINT( ADAM_LV_ERR, "Error: Can't execute python code. (err=%d)\n", ret );
		}
	}

	//getCurrentDateTime(dateTime, sizeof(dateTime), true, true);
	//printf("%s************************* Finish Python *************************\n", dateTime);
	printf("************************* Finish Python *************************\n");

	return;
}

void finalizePython()
{
	Py_Finalize();
	return;
}


/**
 * @brief Handler for the application STOP request from adamCore process
 *        終了イベントハンドラ
 * @param factor   [in] E_ADAM_STOP_FACTOR   Stop factor
 *
 * @note  This handler is executed in Adam thread!
 *        (When the application type is ADAM_APP_TYPE_FREE_STYLE.)
 */
void
stop_handler( E_ADAM_STOP_FACTOR factor )
{
	ADAM_DEBUG_PRINT( ADAM_LV_DBG, "stop app ( factor = %d )\n", factor );

	s_stopFactor = factor;

//	Py_BLOCK_THREADS
#if 1
	do {
		if( factor == ADAM_STOP_FACTOR_APPLICATION ){  break; }

		PyGILStateLock _lock;

		PyObject* pPyStopHandler = PyObject_GetAttrString(s_pAdamModule, "stopCallback");
		if( pPyStopHandler == Py_None ){
			PyErr_Print();
			ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Unset Stop callback function\n");
			break;
		}

		if( !PyCallable_Check(pPyStopHandler) ){
			PyErr_Print();
			ADAM_DEBUG_PRINT(ADAM_LV_DBG, "Python callback is %d\n", PyCallable_Check(pPyStopHandler));
			Py_XDECREF(pPyStopHandler);
			break;
		}

		PyObject* pPyRet = PyObject_CallObject(pPyStopHandler, NULL);
		if( NULL == pPyRet ){
			PyErr_Print();
			ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Stop Callback Exec Error!\n");
			Py_XDECREF(pPyStopHandler);
			break;
		}

		Py_XDECREF(pPyStopHandler);
		Py_XDECREF(pPyRet);
	} while(0);
#endif
//	Py_UNBLOCK_THREADS

	ADAM_Eventloop_Exit(s_systemEventloopId);
	ADAM_DEBUG_PRINT( ADAM_LV_DBG, "ADAM_Eventloop_exit Finish\n" );
	return;
}


/**
 * @brief Handler for the sending application data request from the host ( via adamCore )
 *        アプリデータ受信ハンドラ
 * @param requestId [in] T_ADAM_REQUEST_ID   Request ID
 * @param pData     [in] ST_ADAM_NET_DATA    Received Data
 *
 * @note  This handler is executed in Adam thread!
 	      (When the application type is ADAM_APP_TYPE_FREE_STYLE.)
 */
void
server_request_receive_handler( T_ADAM_REQUEST_ID requestId, ST_ADAM_NET_DATA* pData )
{
	ADAM_DEBUG_PRINT(ADAM_LV_DBG, "Http: Start HTTP callback.\n");

	Py_BLOCK_THREADS
//	ADAM_DEBUG_PRINT(ADAM_LV_DBG, "Py_BLOCK_THREADS\n");
//	ADAM_DEBUG_PRINT(ADAM_LV_DBG, "counter=%d tid=%ld\n", _save->gilstate_counter, _save->thread_id);
#if 1
	do {
		PyGILStateLock _lock;

		PyObject* pHttpHandler = PyObject_GetAttrString(s_pAdamModule, "httpCallback");
		if( pHttpHandler == Py_None ){
			ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Http: Unset HTTP callback function\n");
			break;
		}

		if( !PyCallable_Check(pHttpHandler) ){
			ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Python callback is %d\n", PyCallable_Check(pHttpHandler));
			Py_XDECREF(pHttpHandler);
			break;
		}

		// Make PyBuffer from Image Data
#if PY_VERSION_HEX >= 0x03030000
		PyObject* pMemView = PyMemoryView_FromMemory(static_cast<char*>(pData->m_pData), pData->m_size, PyBUF_READ);
		if( pMemView == NULL ){
			ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Http: Error Create PyMemoryView\n");
			Py_XDECREF(pHttpHandler);
			break;
		}
		PyObject* pHttpData = PyBytes_FromObject(pMemView);
		Py_XDECREF(pMemView);
		if( pHttpData == NULL ){
			ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Http: Error Create PyBytes\n");
			Py_XDECREF(pHttpHandler);
			break;
		}
#else
		PyObject* pBuf = PyBuffer_FromReadWriteMemory(pData->m_pData, pData->m_size);
		if( pBuf == NULL ){
			ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Http: Error Create PyBuffer\n");
			Py_XDECREF(pHttpHandler);
			break;
		}
		PyObject* pHttpData = PyByteArray_FromObject(pBuf);
		Py_XDECREF(pBuf);
		if( pHttpData == NULL ){
			ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Http: Error Create PyByteArray\n");
			Py_XDECREF(pHttpHandler);
			break;
		}
#endif

		ADAM_DEBUG_PRINT(ADAM_LV_DBG, "Http: ----- Start Callback ----- reqId=-0x%" PRIxPTR "type=%d\n", requestId, pData->m_type);

		PyObject* pPyArg = Py_BuildValue("iO", pData->m_type, pHttpData);
		PyObject* pPyRet = PyObject_CallObject(pHttpHandler, pPyArg);

		ADAM_DEBUG_PRINT(ADAM_LV_DBG, "Http: ----- Finish Callback -----\n");

		Py_XDECREF(pPyArg);
		Py_XDECREF(pHttpData);
		Py_XDECREF(pHttpHandler);

		if( NULL == pPyRet ){
			PyErr_Print();
			ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Http: Callback Exec Error!\n");
			break;
		}

		sendHttpResponse(requestId, pPyRet);
		Py_XDECREF(pPyRet);
	} while(false);
#endif
//	ADAM_DEBUG_PRINT(ADAM_LV_DBG, "counter=%d tid=%ld\n", _save->gilstate_counter, _save->thread_id);
//	ADAM_DEBUG_PRINT(ADAM_LV_DBG, "Py_UNBLOCK_THREADS\n");

	Py_UNBLOCK_THREADS
//	ADAM_DEBUG_PRINT(ADAM_LV_DBG, "counter=%d tid=%ld\n", _save->gilstate_counter, _save->thread_id);

	return;
}


void sendHttpResponse(T_ADAM_REQUEST_ID reqId, PyObject* pArg)
{
	PyObject* pHttpHeader = PyTuple_GetItem(pArg, 0);
	PyObject* pHttpBodyTmp = PyTuple_GetItem(pArg, 1);

	ADAM_DEBUG_PRINT(ADAM_LV_DBG, "reqId=0x%" PRIxPTR ", headerType=%s, bodyType=%s\n",
		reqId, Py_TYPE(pHttpHeader)->tp_name, Py_TYPE(pHttpBodyTmp)->tp_name);

#if PY_VERSION_HEX >= 0x03000000
	ADAM_DEBUG_PRINT(ADAM_LV_DBG, "Header -- %s\n", PyUnicode_AsUTF8(pHttpHeader));
#else
	ADAM_DEBUG_PRINT(ADAM_LV_DBG, "Header -- %s\n", PyString_AsString(pHttpHeader));
#endif

	ST_ADAM_HTTP_DATA header;
	header.m_dataType = ADAM_HTTP_DATA_TYPE_BUF;
#if PY_VERSION_HEX >= 0x03000000
	Py_ssize_t size;
	header.m_data.m_buf.m_pData = (void*)PyUnicode_AsUTF8AndSize(pHttpHeader, &size);
	header.m_data.m_buf.m_size = size;
#else
	header.m_data.m_buf.m_pData = PyString_AsString(pHttpHeader);
	header.m_data.m_buf.m_size = PyString_Size(pHttpHeader);
#endif

	ST_ADAM_HTTP_DATA body;
	body.m_dataType = ADAM_HTTP_DATA_TYPE_BUF;
	PyObject *pHttpBody = PyMemoryView_FromObject(pHttpBodyTmp);
	Py_buffer pyBuf;
	PyObject_GetBuffer(pHttpBody, &pyBuf, PyBUF_SIMPLE);

	body.m_data.m_buf.m_pData = pyBuf.buf;
	body.m_data.m_buf.m_size = pyBuf.len;

//	ADAM_DEBUG_PRINT(ADAM_LV_DBG, "Body -- %zu Bytes\n", pyBuf.len);

//	Py_UNBLOCK_THREADS

	E_ADAM_ERR err = ADAM_ServerResponse_SendAsIs(reqId, &header, &body);
	if( ADAM_ERR_OK != err ){
		ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Error: Send Http Response (err=%d)\n", err);
	}

//	Py_BLOCK_THREADS

	Py_XDECREF(pHttpBody);
	PyBuffer_Release(&pyBuf); //HttpCB メモリリーク対応

	return;
}

void appPref_handler(char* const pPrefName[], const unsigned int prefSize)
{

	Py_BLOCK_THREADS
#if 1
	do {
		PyGILStateLock _lock;

		PyObject* pAppPrefHandler = PyObject_GetAttrString(s_pAdamModule, "appPrefCallback");
		if( pAppPrefHandler == Py_None ){
			break;
		}

		if( !PyCallable_Check(pAppPrefHandler) ){
			ADAM_DEBUG_PRINT(ADAM_LV_ERR, "Python callback is illegal (%d)\n", PyCallable_Check(pAppPrefHandler));
			Py_XDECREF(pAppPrefHandler);
			break;
		}

		ADAM_DEBUG_PRINT(ADAM_LV_DBG, "Start AppPref Update callback.\n");

		PyObject* pTuple = PyTuple_New( prefSize );

		for(unsigned int i = 0; i < prefSize; i++){
#if PY_VERSION_HEX >= 0x03000000
			PyObject* pStr = PyUnicode_FromString(pPrefName[i]);
#else
			PyObject* pStr = PyString_FromString(pPrefName[i]);
#endif
			PyTuple_SetItem( pTuple, i, pStr );
#if 0	//[SetItem]はitemの参照権を盗むので解放NG
			Py_XDECREF(pStr);
#endif
		}

		PyObject_CallObject(pAppPrefHandler, pTuple);
		Py_XDECREF(pTuple);
		Py_XDECREF(pAppPrefHandler);

	} while(false);
#endif
	Py_UNBLOCK_THREADS
}

/*! @} */
