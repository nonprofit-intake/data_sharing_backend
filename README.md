# Family Promise of Spokane Data Sharing

## Tech Stack
**Languages**: Python, SQL

**Dependencies**: Pandas, bcrypt, psycopg2

**Services**: Docker, AWS API Gateway, AWS Lambda, AWS S3, AWS CloudWatch ElephantSQL, PostgreSQL


## Architecture
![Non-technical Diagram](./diagrams/non-tech-diagram.png)

Backend deployed serverlessly through AWS API Gateway and AWS Lambda:

![Architecture Diagram](./diagrams/fampromarch.png)

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


## Endpoint - Return User Info

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

## License
MIT
