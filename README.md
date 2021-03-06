# Family Promise of Spokane Data Sharing
## Project Overview
Avista Utilities wants to know if customers that have fallen behind on payments prior to ceasing to be customers have ended up at a homeless shelter. With this information they are building a model that is able to predict when current customers become at risk of homelessness in order to provide them with the resources needed to prevent it.

**Solution**: We designed an API that uses unique identifiers to determine if a previous customer began receiving services from organizations assisting people experiencing homelessness. At the moment, the API only queries from the Family Promise of Spokane database. We are looking to expand to this service to other shelters and service providers.

## Tech Stack
**Languages**: Python, SQL  
**Dependencies**: Pandas, cryptography, psycopg2  
**AWS**: Chalice, Lambda, API Gateway  
**Services**: ElephantSQL  

## Architecture
![Non-technical Diagram](./diagrams/non-tech-diagram.png)

**Note**: The results from the API response also includes individuals with matching last names (ie. other family members) and those last names that were not found in our databases.

![Architecture Diagram](./diagrams/fampromarch.png)

## Development
#### Before starting, make sure you have Python and pip installed
`python --version`  
`pip --version`

If you do not have Python, install latest 3.x version: 
- Official source: [python.org](https://www.python.org/)
- [Installing Python](http://docs.python-guide.org/en/latest/starting/installation/) section of _The Hitchhiker’s Guide to Python_
- Usually you will already have pip on your system or it will be included with your Python installation, otherwise: [install pip](https://pip.pypa.io/en/stable/installing/)

#### Install Pipenv packaging tool
`pip install --user pipenv`

#### Clone repository and initialize a virtual environment
`pipenv shell`

#### Install dependencies
`pipenv install`

#### Configure environment variables in `~/.chalice/config.json`
Request environment variables from your Family Promise IT/Data Systems Manager.
```
{
    "version": "2.0",
    "app_name": "data-sharing-api",
    "stages": {
        "dev": {
            "api_gateway_stage": "api",
            "environment_variables": {
                "DB_HOST": "sample_host",
                "DB_USER": "sample_user",
                "DB_PWD": "sample_pwd",
                "WEB_PWD": "sample_pwd",
                "ENCRYPTION_KEY": "sample_key
            }
        }
    }
}
```

#### Begin local development
`cd data-sharing-api`  
`chalice local`

#### If you want to deploy this service, AWS credentials must be configured first
   - If AWS CLI has already been configured you can skip this step
   - Else credentials can be usually configured at `~/.aws/config` with this content:
      ```
      [default]
      aws_access_key_id=<your-access-key-id>
      aws_secret_access_key=<your-secret-access-key>
      region=<your-region>
      ```
   - More details here: [AWS Command Line Interface](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html)

At this point you should be able to send HTTP requests locally to http://localhost:8000/. To exit the local development server use the command `CTRL+C`. 

In this directory you can also run the tests found in `/tests/test_app.py` by using the command `pytest -v`.

#### Once configured, deploy web service
`chalice deploy`

## Route Overview

**API URL**:
`https://z0arg6enmk.execute-api.us-east-1.amazonaws.com/api/`

### Return guest information

Returns limited information about guests that are found in our databases. Response return both full matches (last name and ssn match) and partial matches (last name matches only) as well as last names from the request that were not found in our databases.

#### Request
`POST /guests`
```
{
    "last_name": [
        "smith", 
        "doe",
        "johnson",
    ],
    "ssn": [
        1234, 
        1234,
        1234
    ],
    "pwd": "sample_password"
}
```

#### Success Responses
```
Status: 200 OK
Content-Type: application/json

{
    "full_matches": [
        {
            "first_name": "john",
            "last_name": "doe"
            "enroll_date": "10-22-2018",
            "exit_date": "10-25-2018",
            "exit_destination": "Rental by client, other ongoing housing subsidy",
            "income_at_entry": 1234.0,
            "income_at_exit": 2234.0,
        }
    ],
   "partial_matches": [
       {
           "first_name": "james",
           "last_name": "smith"
           "enroll_date": "10-22-2018",
           "exit_date": "10-25-2018",
           "exit_destination": "Rental by client, no ongoing housing subsidy",
           "income_at_entry": 1234.0,
           "income_at_exit": 2234.0,
        }
    ],
    "not_found": [
        "johnson"
    ]
}
```

#### Error Responses
```
Status: 400 Bad Request

{
  "Code": "BadRequestError",
  "Message": "BadRequestError: JSON object must be a dictionary"
}
```
```
Status: 400 Bad Request

{
  "Code": "BadRequestError",
  "Message": "BadRequestError: Request JSON object requires 'last_name', 'ssn', and 'pwd' keys"
}
```
```
Status: 400 Bad Request

{
  "Code": "BadRequestError",
  "Message": "BadRequestError: Invalid password"
}
```
```
Status: 400 Bad Request

{
  "Code": "BadRequestError",
  "Message": "BadRequestError: 'last_name' and 'ssn' key values must be of type list"
}
```
```
Status: 400 Bad Request

{
  "Code": "BadRequestError",
  "Message": "BadRequestError: 'last_name' and 'ssn' lists must be of equal length"
}
```
```
Status: 400 Bad Request

{
  "Code": "BadRequestError",
  "Message": "BadRequestError: 'last_name' and 'ssn' lists must have at least one entry"
}
```
```
Status: 400 Bad Request

{
  "Code": "BadRequestError",
  "Message": "BadRequestError: 'ssn' values must all be of type integer"
}
```
```
Status: 400 Bad Request

{
  "Code": "BadRequestError",
  "Message": "BadRequestError: 'last_name' values must all be of type string"
}
```
```
Status: 503 Unavailable

{
    "Message": "Service unavailable at the moment, a request has been made to resolve this issue. Please try again in 5 minutes. If it continues to be unavailable, please reach out to your Family Promise representative"}
```
```
Status: 500 Internal Service Error

{
  "Message": "Service currently unavailable. Please contact your Family Promise representative"
}
```

## License
MIT
