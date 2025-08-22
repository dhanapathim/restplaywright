import json
import os
import yaml
import jsonref
from pathlib import Path
from RestPlaywright.utils import llm


class LLMProcessor:
    def __init__(self, target_folder: str, input_dir: str,language:str,output_dir: str = None):
        self.playwright_dir = Path(target_folder)
        self.input_dir=Path(input_dir)
        print(self.playwright_dir)
        self.output_dir = Path(output_dir) if output_dir else self.playwright_dir/"playwright/tests"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm = llm

    def to_plain_obj(self, obj):
        if isinstance(obj, dict):
            return {k: self.to_plain_obj(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.to_plain_obj(i) for i in obj]
        return obj

    def load_spec(self, file: Path):
        with open(file, "r", encoding="utf-8") as f:
            if file.suffix in [".yaml", ".yml",".json"]:
                raw = yaml.safe_load(f)
            else:
                raw = json.load(f)

        if raw is None:
            raise ValueError(f"File {file.name} is empty or invalid.")
        resolved = jsonref.replace_refs(raw, merge_props=True)
        return self.to_plain_obj(resolved)


    def build_prompt(self, spec: dict, filename: str) -> str:
      self.response_ = f"""
You are an expert in Playwright and API testing.

Input:
I will provide with you.
1. An OpenAPI/Swagger spec (YAML or JSON).
2.A sample Output for style reference.
OpenAPI file: **{filename}**

Task:
Generate a **single Playwright test file in ES6 **{{language}}** (.spec.js)** that covers **all API paths and methods** defined in the spec, following the **same structure, style, and formatting** as the sample `.spec.js` file I provide.

Strict rules for generation:
-Covers **all paths and methods** in the OpenAPI spec.
-Generate a Playwright test in **{{language}}** for the OpenAPI endpoint [METHOD] [PATH].
-Use import {{ expect }} from '@playwright/test'.
-Use import {{ test }} from '../fixtures/apiWithAllure'.
-No comments, no helper functions, no logging, no console output.
-Should be formatted
-Return only the test code without any extra content or explanation.
- Follows the **exact same structure, formatting, naming, and content-style** as the sample .spec.js file.
- Use `@playwright/test` with `request` fixture.
- Identify the `requestBody` content-types and `response` content-types (under `content`) for each API operation.
- Generate **one `test.describe` block for each supported Request → Response content-type combination**.
- **Do not skip any request/response content-type combinations.**
-**Do not skip any API paths and methods in the OpenAPI/Swagger File.
- Use only the content-types explicitly defined in the spec.
- Inside each `test.describe`, generate `test` blocks for every status code defined in the responses.
-Generate Playwright API test code where every test function has the signature: async ({{ request, baseURL}}). The baseURL should be passed as a fixture or global setup, and it must be consumed inside each test using this syntax. Do not use destructuring inside the function body, only in the test signature.
- For **200/201 success codes**:
  - Use request/response **examples from the spec if provided**.
  - If no examples exist, generate reasonable **sample data** for testing.
-I want to generate example API test payloads for the following status codes: 
- For **200/400/404/422/default error codes**: send invalid or missing data to trigger negative cases.
- Print both the **request payload** and the **response body** in each test using `console.log`.
-Generate Playwright API test code where all string assertions (like expect().toContain() or expect().toMatch()) must match the exact case of the actual API response. The test should inspect the API response body and assert against the correct case-sensitive substrings exactly as they appear in the response. Do not assume lowercase or uppercase. Always read and match the actual response structure.
-Some responses have a specific expected response type (e.g., application/json, application/xml,etc.).
-Generate Playwright API tests that validate status codes, response schema, required fields, and handle both success and error responses based on my OpenAPI.
- Validate with Playwright `expect`:
  - `expect(response.status()).toBe(expectedStatus)`
  - If JSON: `expect(body).toHaveProperty(...)`
- Ensure the file is **clean, async/await-based, ready-to-run**.
-Do not include any invalid syntax (e.g., and =>, test.describe, incorrect arrow functions).
-Please check there are no unnecessary line breaks or spacing (e.g. broken const declarations), and that expect().toContain() is used appropriately.
- Output must be a **single .spec.js Playwright test file**, matching the **style and structure of the sample Output I provide.
-Do **NOT** generate tests for other methods.
-Do not add explanations or comments.
-don't put the OpenAPI JSON directly in the content field
-Return only the code block, no extra text or inline comments.

Output:
A single **.spec.js Playwright test file**.
provided a Sample Output as a style reference.

Sample Output:
import {{expect }} from '@playwright/test'
import {{ test }} from '../fixtures/apiWithAllure'


const examplePetJson = {{
  id: 10,
  name: 'doggie',
  category: {{ id: 1, name: 'Dogs' }},
  photoUrls: ['http://example.com/photo1'],
  tags: [{{ id: 1, name: 'tag1' }}],
  status: 'available'
}}

const examplePetXml = `<?xml version="1.0" encoding="UTF-8"?>
  <pet>
    <id>10</id>
    <name>doggie</name>
    <category>
      <id>1</id>
      <name>Dogs</name>
    </category>
    <photoUrls>
      <photoUrl>string</photoUrl>
    </photoUrls>
    <tags>
      <tag>
        <id>0</id>
        <name>string</name>
      </tag>
    </tags>
    <status>available</status>
  </pet>`;

const formUrlEncoded = new URLSearchParams({{
  id: '10',
  name: 'doggie',
  'category.id': '1',
  'category.name': 'Dogs',
  photoUrls: 'http://example.com/photo1',
  'tags[0].id': '1',
  'tags[0].name': 'tag1',
  status: 'available'
}})

const badForm = new URLSearchParams({{ wrong: 'data' }})

// -------------------- 1. JSON → JSON --------------------
test.describe('/pet - POST JSON → JSON', () => {{
  test('200 - Successful operation', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/json',
          'Content-Type': 'application/json',

        }},
        data: examplePetJson
      }})
    
     const body = await response.json()
    console.log('200 JSON→JSON:', body)
    expect(response.status()).toBe(200)
    expect(body).toHaveProperty('id')
    expect(body).toHaveProperty('name', 'doggie')
  }})

  test('400 - Invalid input', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        }},
        data: {{ invalid: 'payload' }}
      }})
    console.log('400 JSON→JSON:', await response.text())
    expect(response.status()).toBeGreaterThanOrEqual(400);

  }})

  test('422 - Validation exception', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/json',
          'Content-Type': 'application/json',

        }},
        data: {{ name: '', photoUrls: [] }}
      }})
    console.log('422 JSON→JSON:', await response.text())
    expect(response.status()).toBeGreaterThanOrEqual(422);
    //expect(response.status()).toBe(422)
  }})

  test('default - Unexpected error', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-Force-Error': 'true'
        }},
        data: {{ invalid: 'Unexpected' }}
      }})
    
    const body = await response.json()
    console.log('Default JSON→JSON:', body)
    expect([500, 501, 502, 503]).toContain(response.status())
    expect(body).toHaveProperty('code')
    expect(body).toHaveProperty('message')
  }})
}})

// -------------------- 2. JSON → XML --------------------
test.describe('/pet - POST JSON → XML', () => {{
  test('200 - Successful operation', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/json',

        }},
        data: examplePetJson
      }})
    const
      text = await response.text()
    console.log('200 JSON→XML:', text)
    expect(response.status()).toBe(200)
    expect(text).toContain('<Pet>')
    expect(text).toContain('<name>doggie</name>')
  }})

  test('400 - Invalid input', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/json',

        }},
        data: {{ wrong: 'input' }}
      }})
    console.log('400 JSON→XML:', await response.text())
    expect(response.status()).toBeGreaterThanOrEqual(400);
    //expect(response.status()).toBe(400)
  }})

  test('422 - Validation exception', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/json',

        }},
        data: {{ name: '', photoUrls: [] }}
      }})
    console.log('422 JSON→XML:', await response.text())
    expect(response.status()).toBeGreaterThanOrEqual(422);
  }})

  test('default - Unexpected error', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/json',
          'X-Force-Error': 'true'
        }},
        data: {{ invalid: 'Unexpected' }}
      }})
    console.log('Default JSON→XML:', await response.text())
    expect([500, 501, 502, 503]).toContain(response.status())
  }})
}})

// -------------------- 3. XML → JSON --------------------
test.describe('/pet - POST XML → JSON', () => {{
  test('200 - Successful operation', async ({{ request, baseURL }}) => {{
    const response = await request.post(`${{baseURL}}/pet`, {{
      headers: {{
        'Accept': 'application/json',
        'Content-Type': 'application/xml',

      }},
      data: examplePetXml
    }})

    const body = await response.json()
    console.log('200 XML→JSON:', body)
    expect(response.status()).toBe(200)
    expect(body).toHaveProperty('id')
    expect(body).toHaveProperty('name', 'doggie')
  }})


  test('400 - Invalid input', async ({{ request, baseURL }}) => {{
    const response = await request.post(`${{baseURL}}/pet`, {{
      headers: {{
        'Accept': 'application/json',
        'Content-Type': 'application/xml',

      }},
      data: ` < invalid > < data / > < / invalid > `
    }})
    console.log('400 XML→JSON:', await response.text())
    expect(response.status()).toBe(400)
  }})

  test('422 - Validation exception', async ({{ request, baseURL }}) => {{

    const response = await request.post(`${{baseURL}}/pet`, {{
      headers: {{
        'Accept': 'application/json',
        'Content-Type': 'application/xml',

      }},
      data: ` < pet > < name > < / name > < photoUrls / > < / pet > `
    }})
    console.log('422 XML→JSON:', await response.text())
    expect(response.status()).toBe(422)
  }})

  test('default - Unexpected error', async ({{ request, baseURL }}) => {{

    const response = await request.post(`${{baseURL}}/pet`, {{
      headers: {{
        'Accept': 'application/json',
        'Content-Type': 'application/xml',

        'X-Force-Error': 'true'
      }},
      data: ` < invalid > < data / > < / invalid > `
    }})

    const body = await response.json()
    console.log('Default XML→JSON:', body)
    expect([500, 501, 502, 503]).toContain(response.status())
    expect(body).toHaveProperty('code')
    expect(body).toHaveProperty('message')
  }})
}})

// -------------------- 4. XML → XML --------------------
test.describe('/pet - POST XML → XML', () => {{
  test('200 - Successful operation', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/xml',

        }},
        data: examplePetXml
      }})
    
     const text = await response.text()
    console.log('200 XML→XML:', text)
    expect(response.status()).toBe(200)
    expect(text).toContain('<Pet>')
    expect(text).toContain('<name>doggie</name>')
  }})

  test('400 - Invalid input', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/xml',

        }},
        data: ` < pet > < invalid > < / invalid > < / pet > `
      }})
    console.log('400 XML→XML:', await response.text())
    expect(response.status()).toBe(400)
  }})

  test('422 - Validation exception', async ({{ request, baseURL }}) => {{
    
    const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/xml',

        }},
        data: ` < pet > < name > < / name > < photoUrls / > < / pet > `
      }})
    console.log('422 XML→XML:', await response.text())
    expect(response.status()).toBe(422)
  }})

  test('default - Unexpected error', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/xml',

          'X-Force-Error': 'true'
        }},
        data: examplePetXml
      }})
    console.log('Default XML→XML:', await response.text())
    expect([500, 501, 502, 503]).toContain(response.status())
  }})
}})

// -------------------- 5. FORM → JSON --------------------
test.describe('/pet - POST FORM → JSON', () => {{
  test('200 - Successful operation', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded',

        }},
        data: formUrlEncoded.toString()
      }})
    
     const body = await response.json()
    console.log('200 FORM→JSON:', body)
    expect(response.status()).toBe(200)
    expect(body).toHaveProperty('id')
    expect(body).toHaveProperty('name', 'doggie')
  }})

  test('400 - Invalid input', async ({{ request, baseURL }}) => {{


    const response = await request.post(`${{baseURL}}/pet`, {{
      headers: {{
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',

      }},
      data: badForm.toString()
    }})
    console.log('400 FORM→JSON:', await response.text())
    expect(response.status()).toBe(400)
  }})

  test('422 - Validation exception', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded',

        }},
        data: new URLSearchParams({{ name: '', photoUrls: '' }}).toString()
      }})
    console.log('422 FORM→JSON:', await response.text())
    expect(response.status()).toBe(422)
  }})

  test('default - Unexpected error', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded',

          'X-Force-Error': 'true'
        }},
        data: badForm.toString()
      }})
    const
      body = await response.json()
    console.log('Default FORM→JSON:', body)
    expect([500, 501, 502, 503]).toContain(response.status())
    expect(body).toHaveProperty('code')
    expect(body).toHaveProperty('message')
  }})
}})

// -------------------- 6. FORM → XML --------------------
test.describe('/pet - POST FORM → XML', () => {{
  test('200 - Successful operation', async ({{ request, baseURL }}) => {{
    const
      response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/x-www-form-urlencoded',

        }},
        data: formUrlEncoded.toString()
      }})
    const
      text = await response.text()
    console.log('200 FORM→XML:', text)
    expect(response.status()).toBe(200)
    expect(text).toContain('<Pet>')
    expect(text).toContain('<name>doggie</name>')
  }})

  test('400 - Invalid input', async ({{ request, baseURL }}) => {{
    const
      badForm = new
        URLSearchParams({{ wrong: 'data' }})
    const
      response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/x-www-form-urlencoded',

        }},
        data: badForm.toString()
      }})
    console.log('400 FORM→XML:', await response.text())
    expect(response.status()).toBe(400)
  }})

  test('422 - Validation exception', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/x-www-form-urlencoded',


        }},
        data: new URLSearchParams({{ name: '', photoUrls: '' }}).toString()
      }})
    console.log('422 FORM→XML:', await response.text())
    expect(response.status()).toBe(422)
  }})

  test('default - Unexpected error', async ({{ request, baseURL }}) => {{
    
     const response = await request.post(`${{baseURL}}/pet`, {{
        headers: {{
          'Accept': 'application/xml',
          'Content-Type': 'application/x-www-form-urlencoded',

          'X-Force-Error': 'true'
        }},
        data: badForm.toString()
      }})
    console.log('Default FORM→XML:', await response.text())
    expect([500, 501, 502, 503]).toContain(response.status())
  }})
}})


{json.dumps(spec, indent=2)}
"""
      return self.response_


    def run(self):
        for file in self.input_dir.iterdir():
            if file.suffix.lower() not in [".json", ".yaml", ".yml"]:
                continue
            try:
                print(f"📄 Processing {file.name}")
                spec = self.load_spec(file)
                prompt = self.build_prompt(spec, file.name)

                assert isinstance(prompt, str), "Prompt must be a string"
                print(f"\n🧠 Prompt preview for {file.name}:\n{prompt[:300]}...\n")

                response = self.llm.invoke(prompt)


                with open(self.output_dir / f"{file.stem}.spec.js", "w", encoding="utf-8") as f:
                    f.write(response.content)
                clean_code_fences(self.output_dir)

                print(f"✅ Saved LLM response for {file.name}")

            except Exception as e:
                print(f"❌ Failed to process {file.name}: {e}")


class GlobalSetup:
    def __init__(self, target_folder: str, swagger_file: str, output_dir: str = None):
        self.playwright_dir = Path(target_folder)
        self.swagger_file = Path(swagger_file)
        self.output_dir = Path(output_dir) if output_dir else self.playwright_dir / "playwright"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm = llm

    def load_spec(self):
        with open(self.swagger_file, "r", encoding="utf-8") as f:
            if self.swagger_file.suffix.lower() in [".yaml", ".yml"]:
                spec = yaml.safe_load(f)
                return yaml.dump(spec)
            elif self.swagger_file.suffix.lower() == ".json":
                spec = json.load(f)
                return json.dumps(spec, indent=2)
            else:
                raise ValueError("Unsupported Swagger file format.")

    def build_global_setup_prompt(self, spec: dict, filename: str) -> str:
        return f"""
        You are an expert in Playwright and API testing.

        Input:
        I will provide you with:
        1. An OpenAPI/Swagger spec (YAML or JSON).
        OpenAPI file: {{filename}}
        2.From it, detect the authentication method(s) in `securitySchemes` and global `security`.
        Task:
        1. Detect all authentication methods in `components.securitySchemes` and `security`.
        2. Don't Write the securitySchemes in the global_Setup.js
        3. Generate a `global-setup.js` file for Playwright that configures authentication globally based on the detected scheme(s):
          - If `apiKey` → read API key from `process.env`, set it in `extraHTTPHeaders`, save to `auth.json`.
          - If `http` basic → read username/password from `process.env`, save to `auth.json`.
          - If OAuth2 → simulate token retrieval or placeholder, save token to `auth.json`.


        Rules:
       - Code must be valid ES modules (ESM).
       -The first two lines of the file must be:
          import dotenv from 'dotenv';
          dotenv.config();
       - Do not print print the open Api spect.
       - Do not hardcode sensitive values — use `process.env` with placeholder names.
       - Include error handling if no credentials are set.
       - Do not add explanations or comments.
       - don't put the OpenAPI JSON directly in the content field
       - don't Write the securitySchemes in the global_Setup.js

    The code should be valid ES modules (ESM) and work directly with `@playwright/test`.


import dotenv from 'dotenv';
import fs from 'fs';
import on from os;
import path from 'path';
dotenv.config();

const STORAGE_STATE_PATH = path.join(process.cwd(), 'auth.json');

async function globalSetup() {{
  const authData = {{ extraHTTPHeaders: {{}} }};

  
  const API_KEY_VALUE = process.env.API_KEY_VALUE;
  if (API_KEY_VALUE) {{
    authData.extraHTTPHeaders['api_key'] = API_KEY_VALUE;
  }}

  const OAUTH_ACCESS_TOKEN = process.env.OAUTH_ACCESS_TOKEN;
  if (OAUTH_ACCESS_TOKEN) {{
    authData.extraHTTPHeaders['Authorization'] = `Bearer ${{OAUTH_ACCESS_TOKEN}}`;
  }}

  const BASIC_AUTH_USERNAME = process.env.BASIC_AUTH_USERNAME;
  const BASIC_AUTH_PASSWORD = process.env.BASIC_AUTH_PASSWORD;
  if (BASIC_AUTH_USERNAME && BASIC_AUTH_PASSWORD) {{
    const credentials = Buffer.from(`${{BASIC_AUTH_USERNAME}}:${{BASIC_AUTH_PASSWORD}}`).toString('base64');
    authData.extraHTTPHeaders['Authorization'] = `Basic ${{credentials}}`;
  }} else if (BASIC_AUTH_USERNAME || BASIC_AUTH_PASSWORD) {{
    throw new Error('Both BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD must be set for HTTP Basic authentication.');
  }}

  if (Object.keys(authData.extraHTTPHeaders).length === 0) {{
    throw new Error('No authentication credentials found. Please set API_KEY_VALUE, OAUTH_ACCESS_TOKEN, or BASIC_AUTH_USERNAME/PASSWORD environment variables.');
  }}

  fs.writeFileSync(
    STORAGE_STATE_PATH,
    JSON.stringify(authData, null, 2)
  );

  //const envFilePath = "./allure-results/environment.properties";
const resultsDir = path.join(__dirname, "allure-results");
  const envFilePath = path.join(resultsDir, "environment.properties");

  // Ensure allure-results directory exists
  if (!fs.existsSync(resultsDir)) {{
    fs.mkdirSync(resultsDir, {{ recursive: true }});
  }}
  const envData = [
    `OS=${{os.type()}} ${{os.release()}}`,
    `Node=${{process.version}}`,
    `BaseURL=${{process.env.BASE_URL || "http://localhost:3000"}}`,
    `Browser=Playwright Default`,
    `Project=PetStore`,
    `Organization=Accion Labs`,
  ].join("\n");

  fs.writeFileSync(envFilePath, envData, "utf-8");
}}

export default globalSetup;


     OpenAPI Spec:
    {json.dumps(spec, indent=2)}
    """

    def genarateglobalsetup(self):
        spec = self.load_spec()
        GlobalSetup = self.build_global_setup_prompt(spec, self.swagger_file)
        response = self.llm.invoke(GlobalSetup)

        with open(self.output_dir / "global-setup.js", "w", encoding="utf-8") as f:
            f.write(response.content)
        clean_code_fences(self.output_dir)

def clean_code_fences(root_folder, extensions=[".js", ".ts",]):
    for subdir, _, files in os.walk(root_folder):
        for filename in files:
            if any(filename.endswith(ext) for ext in extensions):
                file_path = os.path.join(subdir, filename)

                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Remove starting and ending Markdown code fences
                if lines and lines[0].strip() == "```javascript":
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]

                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

    print(f"✅ Cleaned all files in: {root_folder}")
