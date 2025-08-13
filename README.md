# restplaywright
Convert Swagger to REST API Automation tests
atdd
- This is a `GenAI-powered` tool that enables the automatic generation of `automation test scripts` using `Gherkin syntax`. 
The tool takes Swagger file as input and transforms them into playwright test scripts. Based on these, it auto-generates the corresponding test automation scripts, helping teams `accelerate test development`, ensure `consistency`, and `reduce manual effort` in writing repetitive automation test scripts. 

### Working flow

### Setup
### Required env vars
```txt
SWAGGER_FILE_PATH=/Users/sandhyaranikande/swagger.yml //path of the swagger file 
TARGET_FOLDER=/Users/sandhyaranikande/SampleTest // where the genrated automation scripts should saved
LLM_MODEL=gemini-2.0-flash-thinking-exp-1219 //llm model
LLM_MODEL_PROVIDER=google_genai //llm provide
GEMINI_API_KEY= //api key of llm
TARGET_LANGUAGE=JavaScript 
```

### Steps to generate automation scripts :
- Save the swagger file in local system.
- Configure the required environment variables and install dependencies by executing: `pip install -r requirements.txt`  
- On execution `(python3 main.py)`, the playwright project will be generated with all tests(separate test file for each and every path and its corresponding http method )
- The scripts project `STRUCTURE` will be like this post generation : (Note: the character `/` in the path will be replaced with `_' )
```txt
playwright/
├── node_modules
├── package-lock.json
└── package.json
└──palywright.config.js
└──tests
    ├── path_httpMethod.spec.js
    ├── path_httpMethod.spec.js
```
Example:
```text
playwright/
├── node_modules
├── package-lock.json
└── package.json
└──palywright.config.js
└──tests
    ├── pet_findByStatus_GET.spec.js
    ├── path_findByTags_GET.spec.js
    ├── path_POST.spec.js
    ├── path_GET.spc.js
    
### Run the generated automation scripts
- Note: Some small changes might needs to be done before running the scrips.
- run `npx playwright test`

### Steps to create the wheel file.
- Make sure you have Python 3 + and pip
- Run `python3 -m build --wheel` it will generate the wheel file in  dist folder (`/dist/**.whl`).

### Steps to run the wheel file.
- Make sure you have Python 3 + , pip and node
- get/copy the wheel file into local system
- Create new python env `python3 -m venv .venv` and activate it `source <PATH_TO_.ENV>/bin/activate`
- Run `pip install <PATH_OF_THE_WHEEL_FILE>` (Optional add --force-reinstall as an option).


```
