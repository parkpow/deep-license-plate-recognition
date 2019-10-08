#include "curl/curl.h"
#include <iostream>
#include <string>
#include "json/json/json.h"
#include "json/jsoncpp.cpp"
#include <fstream>

using namespace std;

namespace
{
		size_t callback(
		const char* in,
		std::size_t size,
		std::size_t num,
		std::string* out)
	{
		const size_t totalBytes(size * num);
		out->clear();
		out->append(in, totalBytes);
		return totalBytes;
	}
}

Json::Value sendRequest(string auth_token, string fileName) {
	
	curl_global_init(CURL_GLOBAL_ALL);

	
	curl_off_t speed_upload, total_time;
	curl_mime *form = NULL;
	curl_mimepart *field = NULL;

	CURL *hnd = curl_easy_init();

	//curl_easy_setopt(hnd, CURLOPT_CUSTOMREQUEST, "POST");
	curl_easy_setopt(hnd, CURLOPT_URL, "https://api.platerecognizer.com/v1/plate-reader/");

	form = curl_mime_init(hnd); //initialize form fields

	/* Fill in the file upload field */
	field = curl_mime_addpart(form);
	curl_mime_name(field, "upload");
	curl_mime_filedata(field, fileName.c_str());
	curl_easy_setopt(hnd, CURLOPT_MIMEPOST, form);

	struct curl_slist *headers = NULL;
	headers = curl_slist_append(headers, "cache-control: no-cache");
	headers = curl_slist_append(headers, ("Authorization: Token "+ auth_token).c_str());
	curl_easy_setopt(hnd, CURLOPT_HTTPHEADER, headers);
	unique_ptr<std::string> httpData(new std::string()); //initializing string pointer to  get data
	// Hook up data handling function.
	curl_easy_setopt(hnd, CURLOPT_WRITEFUNCTION, callback);

	// Hook up data container (will be passed as the last parameter to the
	// callback handling function).  Can be any pointer type, since it will
	// internally be passed as a void pointer.
	curl_easy_setopt(hnd, CURLOPT_WRITEDATA, httpData.get());

	CURLcode ret = curl_easy_perform(hnd); //perform the request

	if (ret != CURLE_OK) { //failed case
		fprintf(stderr, "curl_easy_perform() failed: %s\n",
			curl_easy_strerror(ret));
	}
	else {
		/* now extract transfer info */
		curl_easy_getinfo(hnd, CURLINFO_SPEED_UPLOAD_T, &speed_upload);
		curl_easy_getinfo(hnd, CURLINFO_TOTAL_TIME_T, &total_time);

		fprintf(stderr, "Speed: %" CURL_FORMAT_CURL_OFF_T " bytes/sec during %"
			CURL_FORMAT_CURL_OFF_T ".%06ld seconds\n",
			speed_upload,
			(total_time / 1000000), (long)(total_time % 1000000));
	}

	curl_easy_cleanup(hnd); 
	curl_mime_free(form);

	Json::Value jsonData;
	Json::Reader jsonReader;

	if (jsonReader.parse(*httpData, jsonData))
	{
		cout << jsonData;
	}
	else
	{
		std::cout << "Could not parse HTTP data as JSON" << std::endl;
		std::cout << "HTTP data was:\n" << *httpData.get() << std::endl;
	}

	return jsonData;
}



int main(int argc, char *argv[])
{
	string token = "MY_API_KEY";
	Json::Value data;
	if (argc == 2) {
		data = sendRequest(token, argv[1]);
	}
	else {
		cout << "Error:Invalid Arguments!\nUsage: program.exe <Image>";
	}

	ofstream file;
	file.open("responce.txt", ios::app);
	file << data;
	file << "\n\n";
	file.close();
	cout << "\n\n";
	//system("PAUSE");
	return 0;
}
