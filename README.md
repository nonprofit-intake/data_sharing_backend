# Family Promise of Spokane Data Engineering

## Tech Stack
Languages: Python, SQL

Backend: Docker, AWS API Gateway, AWS Lambda, AWS S3, ElephantSQL, PostgreSQL, Pandas, bcrypt

## Getting Started
### Deployment to AWS
#### Developer environment
Build Amazon Linux image with Python 3.7 and pip

```docker build -t example_image_name .```

#### Installing dependencies

All dependencies are already installed, but if for some reason you needed to delete and reinstall:

```docker run -v $(pwd):/aws -ti example_image_name```

then

```pip install bcrypt aws-psycopg2 pandas -t /aws```

Do not install if these packages already exist in the aws folder.

#### Packaging Lambda Function
```zip -r example_filename.zip *```

At this point you'll want to head over the AWS GUI for function creation at AWS Lambda. 

## Development
### Architecture
<img src="https://github.com/nonprofit-intake/data_engineering/blob/main/images/fampromarch.png" width="500" height="350">
Backend deployed serverlessly through AWS API Gateway and AWS Lambda.

### Endpoint - Return User Info

**URL**

https://3yk0fzdvdh.execute-api.us-east-1.amazonaws.com/default/return_user_info

**Description**

Returns the last name, first name, enroll date, exit date, income at entry, income at exit, and exit destination of a user in database.

#### POST Request
```javascript
{
    "last_name": [
        string, 
        string
    ],
    "ssn": [
        string, 
        string
    ],
    "pwd": string
}
```

**Response**
```javascript
{
    "complete_matches": [
        {
            "enroll_date": string,
            "exit_date": string,
            "exit_destination": string,
            "first_name": string,
            "income_at_entry": float,
            "income_at_exit": float,
            "last_name": string
        }
    ],
   "partial_matches": [
       {
           "enroll_date": string,
           "exit_date": string,
           "exit_destination": string,
           "first_name": string,
           "income_at_entry": float,
           "income_at_exit": float,
           "last_name": string
        }
    ]
}
```

#### AWS Environment Variables
- HOST = database URL
- USER = username
- PASSWORD = password
- AUTH_PWD = secret key
