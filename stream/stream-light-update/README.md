# Stream Light Update
1. Install requirements
```shell
pip install -r requirements.txt
```
2. On machine 1 that is online, run script to **extract** the models and code from the Docker image.
```shell
python main.py extract -s platerecognizer/alpr-stream:1.53.0 -d platerecognizer/alpr-stream:1.52.0 -o /tmp/extracted_content
```

You will now have the following folder structure in `/tmp/extracted_content`
```shell
/tmp/extracted_content
├── dest
│   ├── app.tar
│   ├── dist-packages.tar
│   └── site-packages.tar
├── diff
│   ├── app.tar
│   ├── dist-packages.tar
│   └── site-packages.tar
└── source
    ├── app.tar
    ├── dist-packages.tar
    └── site-packages.tar

4 directories, 9 files
```

3. Copy the **diff** folder(`/tmp/extracted_content/diff`) to machine 2 that is offline.

4. On machine 2, run script again to **restore** the content and create a new Docker image.
```shell
python main.py restore -s /tmp/extracted_content/diff -d platerecognizer/alpr-stream:1.52.0 -o latest3
```
Updated image to use will now be called `platerecognizer/alpr-stream:latest3` that you can use to rebuild Stream container
> We recommend using a new tag so that you can have your previous image available to restore to in case of an issue
