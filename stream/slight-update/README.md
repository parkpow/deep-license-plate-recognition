# Stream Slight Update
1. Install requirements
```shell
pip install -r requirements.txt
```
2. On machine 1 that is online, run a script to extract the models and code from the Docker image.
```shell
python main.py extract -i platerecognizer/alpr-stream:1.53.0 -o /tmp/extracted_content
```
You will now have `app.tar`, `dist-packages.tar` and `site-packages.tar` in `/tmp/extracted_content`
3. Copy `/tmp/extracted_content` to machine 2 that is offline.
4. On machine 2, run a script to restore the content and create a new Docker image.
```shell
python main.py restore -i platerecognizer/alpr-stream:1.52.0 -o /tmp/extracted_content -t latest3
```
Updated image to use will now be called `platerecognizer/alpr-stream:latest3`

