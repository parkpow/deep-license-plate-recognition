### Webhook via AWS Lambda example

This guide aims to provide you with a minimum sample to receive webhook data from Snapshot/Stream on your AWS Lambda
instance.

#### Create Lambda function

1. Open Lambda on your AWS dashboard.
2. Click "Create function".
![readme_images/lambda_create_function.png](readme_images/lambda_create_function.png)
3. Fill the function name with "test_webhook". Select Python 3.10 for the Runtime, then click "Create function".
![readme_images/lambda_create_function_detail.png](readme_images/lambda_create_function_detail.png)
4. Inside the code editor, replace the content with the code from [lambda_function.py](./lambda_function.py). This code sample will receive
   webhook data and log them into CloudWatch.
5. Click Deploy
![readme_images/lambda_code_editor.png](readme_images/lambda_code_editor.png)

### Create API gateway

1. Open API Gateway dashboard in AWS.
2. Click "Create API"
![readme_images/api_create.png](readme_images/api_create.png)
3. Click the "Build" button for HTTP API.
![readme_images/api_select_http.png](readme_images/api_select_http.png)
4. Click "Add integration", then select Lambda.
5. In the "Lambda function" text box, search for the function you created earlier.
6. Fill "API name" with "test_api". Then click the "Next" button.
![readme_images/api_configure.png](readme_images/api_configure.png)
7. Select "POST" as the Method. Click "Next".
![readme_images/api_method.png](readme_images/api_method.png)
8. We are going to skip creating Stages, so click "Next" again and then click "Create".
![readme_images/api_review.png](readme_images/api_review.png)
9. On the left side menu, click the link "API: test_api".
![readme_images/api_overview.png](readme_images/api_overview.png)
10. Copy the "Invoke URL". Put this url into your Snapshot/Stream webhook configuration and append it
    with `/test_webhook`.
![readme_images/api_invoke_url.png](readme_images/api_invoke_url.png)

### CloudWatch logs
1. Open "CloudWatch" in AWS.
2. Open Logs > Log groups.
3. Click the log group for "test_webhook".
![readme_images/cloudwatch_log_group.png](readme_images/cloudwatch_log_group.png)
4. When your webhook receive new data, it will log the basic information about the vehicle here.