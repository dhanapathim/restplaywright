import json
import os
import re

import yaml
import jsonref
from pathlib import Path
from utils import llm



class LLMProcessor:
    def __init__(self, target_folder: str, input_dir: str, language:str,output_dir: str = None):
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
OpenAPI file: {{filename}}

Task:
Generate a **single Playwright test file in ES6 {{language}} (.spec.js)** that covers **all API paths and methods** defined in the spec, following the **same structure, style, and formatting** as the sample `.spec.js` file I provide.

Strict rules for generation:
- Covers **all paths and methods** in the OpenAPI spec.
-Generate a Playwright test in {{language}} for the OpenAPI endpoint [METHOD] [PATH].
-Use import {{ test, expect }} from '@playwright/test'.
-No comments, no helper functions, no logging, no console output.
-Return only the test code without any extra content or explanation.
- Follows the **exact same structure, formatting, naming, and content-style** as the sample .spec.js file.
- Use `@playwright/test` with `request` fixture.
- Add `test.use({{ baseURL }})` from the `servers` section of the spec.
- Identify the `requestBody` content-types and `response` content-types (under `content`) for each API operation.
- Generate **one `test.describe` block for each supported Request → Response content-type combination**.
- **Do not skip any request/response content-type combinations.**
-**Do not skip any API paths and methods in the OpenAPI/Swagger JSON.
- Use only the content-types explicitly defined in the spec.
- Inside each `test.describe`, generate `test` blocks for every status code defined in the responses.
- For **200/201 success codes**:
  - Use request/response **examples from the spec if provided**.
  - If no examples exist, generate reasonable **sample data** for testing.
- For **400/404/422/default error codes**: send invalid or missing data to trigger negative cases.
- Print both the **request payload** and the **response body** in each test using `console.log`.
- Validate with Playwright `expect`:
  - `expect(response.status()).toBe(expectedStatus)`
  - If JSON: `expect(body).toHaveProperty(...)`
- Add authentication headers if defined in `securitySchemes` (API key, bearer token, basic auth).
- Ensure the file is **clean, async/await-based, ready-to-run**.
-Do not include any invalid syntax (e.g., and = >, test.describe, incorrect arrow functions).
-Please check that the arrow function syntax is correctly written as =>, there are no unnecessary line breaks or spacing (e.g. broken const declarations), and that expect().toContain() is used appropriately.
- Output must be a **single .spec.js Playwright test file**, matching the **style and structure of the sample file** I provide.
- Do not add explanations or comments.
- don't put the OpenAPI JSON directly in the content field
-Return only the code block, no extra text or inline comments.

Output:
A single **.spec.js Playwright test file**.
provided a Sample Output as a style reference.

Sample Output:
import {{test, expect}} from '@playwright/test'

test.use({{ baseURL: 'https://petstore3.swagger.io/api/v3' }})

const API_KEY = 'special-key'
        const
        BEARER_TOKEN = 'Bearer dummy-oauth-token'

        const
        examplePetJson = {{
          id: 10,
          name: 'doggie',
          category: {{id: 1, name: 'Dogs'}},
          photoUrls: ['http://example.com/photo1'],
          tags: [{{id: 1, name: 'tag1'}}],
          status: 'available'
        }}

        const
        examplePetXml = `
                        < pet >
                        < id > 10 < / id >
                                      < name > doggie < / name >
                                                          < category >
                                                          < id > 1 < / id >
                                                                       < name > Dogs < / name >
                                                                                         < / category >
                                                                                             < photoUrls >
                                                                                             < photoUrl > http://example.com/photo1</photoUrl>
  </photoUrls>
  <tags>
    <tag>
      <id>1</id>
      <name>tag1</name>
    </tag>
  </tags>
  <status>available</status>
</pet>
`

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

// -------------------- 1. JSON → JSON --------------------
test.describe('/pet - POST JSON → JSON', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'api_key': API_KEY,
            'Authorization': BEARER_TOKEN
          }},
          data: examplePetJson
        }})
        const
        body = await response.json()
        console.log('200 JSON→JSON:', body)
        expect(response.status()).toBe(200)
        expect(body).toHaveProperty('id')
        expect(body).toHaveProperty('name', 'doggie')
        }})

        test('400 - Invalid input', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }},
          data: {{invalid: 'payload'}}
        }})
        console.log('400 JSON→JSON:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }},
          data: {{name: '', photoUrls: []}}
        }})
        console.log('422 JSON→JSON:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Force-Error': 'true'
          }},
          data: examplePetJson
        }})
        console.log('Default JSON→JSON:', await response.text())
        expect([500, 501, 502, 503]).toContain(response.status())
        }})
        }})

// -------------------- 2. JSON → XML --------------------
test.describe('/pet - POST JSON → XML', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/json'
          }},
          data: examplePetJson
        }})
        const
        text = await response.text()
        console.log('200 JSON→XML:', text)
        expect(response.status()).toBe(200)
        expect(text).toContain('<pet>')
        }})

        test('400 - Invalid input', async ({{request}}) = > {{
          const
        response =
        return self.response_
        await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/json'
          }},
          data: {{wrong: 'input'}}
        }})
        console.log('400 JSON→XML:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/json'
          }},
          data: {{name: '', photoUrls: []}}
        }})
        console.log('422 JSON→XML:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/json',
            'X-Force-Error': 'true'
          }},
          data: examplePetJson
        }})
        console.log('Default JSON→XML:', await response.text())
        expect([500, 501, 502, 503]).toContain(response.status())
        }})
        }})

// -------------------- 3. XML → JSON --------------------
test.describe('/pet - POST XML → JSON', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/xml'
          }},
          data: examplePetXml
        }})
        const
        body = await response.json()
        console.log('200 XML→JSON:', body)
        expect(response.status()).toBe(200)
        expect(body).toHaveProperty('id')
        expect(body).toHaveProperty('name')
        }})

        test('400 - Invalid input', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/xml'
          }},
          data: ` < invalid > < data / > < / invalid > `
        }})
        console.log('400 XML→JSON:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/xml'
          }},
          data: ` < pet > < name > < / name > < photoUrls / > < / pet > `
        }})
        console.log('422 XML→JSON:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/xml',
            'X-Force-Error': 'true'
          }},
          data: examplePetXml
        }})
        console.log('Default XML→JSON:', await response.text())
        expect([500, 501, 502, 503]).toContain(response.status())
        }})
        }})

// -------------------- 4. XML → XML --------------------
test.describe('/pet - POST XML → XML', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/xml'
          }},
          data: examplePetXml
        }})
        const
        text = await response.text()
        console.log('200 XML→XML:', text)
        expect(response.status()).toBe(200)
        expect(text).toContain('<pet>')
        }})

        test('400 - Invalid input', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/xml'
          }},
          data: ` < pet > < invalid > < / invalid > < / pet > `
        }})
        console.log('400 XML→XML:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/xml'
          }},
          data: ` < pet > < name > < / name > < photoUrls / > < / pet > `
        }})
        console.log('422 XML→XML:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
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
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: formUrlEncoded.toString()
        }})
        const
        body = await response.json()
        console.log('200 FORM→JSON:', body)
        expect(response.status()).toBe(200)
        expect(body).toHaveProperty('id')
        expect(body).toHaveProperty('name')
        }})

        test('400 - Invalid input', async ({{request}}) = > {{
          const
        badForm = new
        URLSearchParams({{wrong: 'data'}})
        const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: badForm.toString()
        }})
        console.log('400 FORM→JSON:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: new URLSearchParams({{name: '', photoUrls: ''}}).toString()
        }})
        console.log('422 FORM→JSON:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Force-Error': 'true'
          }},
          data: formUrlEncoded.toString()
        }})
        console.log('Default FORM→JSON:', await response.text())
        expect([500, 501, 502, 503]).toContain(response.status())
        }})
        }})

// -------------------- 6. FORM → XML --------------------
test.describe('/pet - POST FORM → XML', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: formUrlEncoded.toString()
        }})
        const
        text = await response.text()
        console.log('200 FORM→XML:', text)
        expect(response.status()).toBe(200)
        expect(text).toContain('<pet>')
        }})

        test('400 - Invalid input', async ({{request}}) = > {{
          const
        badForm = new
        URLSearchParams({{wrong: 'data'}})
        const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: badForm.toString()
        }})
        console.log('400 FORM→XML:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: new URLSearchParams({{name: '', photoUrls: ''}}).toString()
        }})
        console.log('422 FORM→XML:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.post('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Force-Error': 'true'
          }},
          data: formUrlEncoded.toString()
        }})
        console.log('Default FORM→XML:', await response.text())
        expect([500, 501, 502, 503]).toContain(response.status())
        }})
        }})


// -------------------- 7. JSON → JSON --------------------
test.describe('/pet - PUT JSON → JSON', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'api_key': API_KEY,
            'Authorization': BEARER_TOKEN
          }},
          data: examplePetJson
        }})
        const
        body = await response.json()
        console.log('200 PUT JSON→JSON:', body)
        expect(response.status()).toBe(200)
        expect(body).toHaveProperty('id')
        expect(body).toHaveProperty('name', 'doggie')
        }})

        test('400 - Invalid ID supplied', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }},
          data: {{wrong: 'data'}}
        }})
        console.log('400 PUT JSON→JSON:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('404 - Pet not found', async ({{request}}) = > {{
          const
        payload = {{...
        examplePetJson, id: 99999999}}
        const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }},
          data: payload
        }})
        console.log('404 PUT JSON→JSON:', await response.text())
        expect(response.status()).toBe(404)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }},
          data: {{name: '', photoUrls: []}}
        }})
        console.log('422 PUT JSON→JSON:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Force-Error': 'true'
          }},
          data: examplePetJson
        }})
        console.log('Default PUT JSON→JSON:', await response.text())
        expect([500, 501, 502, 503]).toContain(response.status())
        }})
        }})

// -------------------- 8. JSON → XML --------------------
test.describe('/pet - PUT JSON → XML', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/json'
          }},
          data: examplePetJson
        }})
        const
        text = await response.text()
        console.log('200 PUT JSON→XML:', text)
        expect(response.status()).toBe(200)
        expect(text).toContain('<pet>')
        }})

        test('400 - Invalid ID supplied', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/json'
          }},
          data: {{invalid: 'input'}}
        }})
        console.log('400 PUT JSON→XML:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('404 - Pet not found', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/json'
          }},
          data: {{...examplePetJson, id: 99999999}}
        }})
        console.log('404 PUT JSON→XML:', await response.text())
        expect(response.status()).toBe(404)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/json'
          }},
          data: {{name: '', photoUrls: []}}
        }})
        console.log('422 PUT JSON→XML:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/json',
            'X-Force-Error': 'true'
          }},
          data: examplePetJson
        }})
        console.log('Default PUT JSON→XML:', await response.text())
        expect([500, 501, 502, 503]).toContain(response.status())
        }})
        }})

// -------------------- 9. XML → JSON --------------------
test.describe('/pet - PUT XML → JSON', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/xml'
          }},
          data: examplePetXml
        }})
        const
        body = await response.json()
        console.log('200 PUT XML→JSON:', body)
        expect(response.status()).toBe(200)
        expect(body).toHaveProperty('id')
        expect(body).toHaveProperty('name')
        }})

        test('400 - Invalid ID supplied', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/xml'
          }},
          data: ` < invalid > bad < / invalid > `
        }})
        console.log('400 PUT XML→JSON:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('404 - Pet not found', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/xml'
          }},
          data: ` < pet > < id > 99999999 < / id > < name > ghost < / name > < photoUrls > < photoUrl > url < / photoUrl > < / photoUrls > < / pet > `
        }})
        console.log('404 PUT XML→JSON:', await response.text())
        expect(response.status()).toBe(404)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/xml'
          }},
          data: ` < pet > < name > < / name > < photoUrls / > < / pet > `
        }})
        console.log('422 PUT XML→JSON:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/xml',
            'X-Force-Error': 'true'
          }},
          data: examplePetXml
        }})
        console.log('Default PUT XML→JSON:', await response.text())
        expect([500, 501, 502, 503]).toContain(response.status())
        }})
        }})

// -------------------- 10. XML → XML --------------------
test.describe('/pet - PUT XML → XML', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/xml'
          }},
          data: examplePetXml
        }})
        const
        text = await response.text()
        console.log('200 PUT XML→XML:', text)
        expect(response.status()).toBe(200)
        expect(text).toContain('<pet>')
        }})

        test('400 - Invalid ID supplied', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/xml'
          }},
          data: ` < invalid > < bad / > < / invalid > `
        }})
        console.log('400 PUT XML→XML:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('404 - Pet not found', async  ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/xml'
          }},
          data: ` < pet > < id > 99999999 < / id > < name > ghost < / name > < photoUrls > < photoUrl > url < / photoUrl > < / photoUrls > < / pet > `
        }})
        console.log('404 PUT XML→XML:', await response.text())
        expect(response.status()).toBe(404)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/xml'
          }},
          data: ` < pet > < name > < / name > < photoUrls / > < / pet > `
        }})
        console.log('422 PUT XML→XML:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/xml',
            'X-Force-Error': 'true'
          }},
          data: examplePetXml
        }})
        console.log('Default PUT XML→XML:', await response.text())
        expect([500, 501, 502, 503]).toContain(response.status())
        }})
        }})

// -------------------- 11. FORM → JSON --------------------
test.describe('/pet - PUT FORM → JSON', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: formUrlEncoded.toString()
        }})
        const
        body = await response.json()
        console.log('200 PUT FORM→JSON:', body)
        expect(response.status()).toBe(200)
        expect(body).toHaveProperty('id')
        expect(body).toHaveProperty('name')
        }})

        test('400 - Invalid ID supplied', async ({{request}}) = > {{
          const
        badForm = new
        URLSearchParams({{wrong: 'value'}})
        const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: badForm.toString()
        }})
        console.log('400 PUT FORM→JSON:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('404 - Pet not found', async ({{request}}) = > {{
          const
        form = new
        URLSearchParams({{id: '99999999', name: 'Ghost', photoUrls: 'url'}})
        const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: form.toString()
        }})
        console.log('404 PUT FORM→JSON:', await response.text())
        expect(response.status()).toBe(404)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        form = new
        URLSearchParams({{name: '', photoUrls: ''}})
        const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: form.toString()
        }})
        console.log('422 PUT FORM→JSON:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Force-Error': 'true'
          }},
          data: formUrlEncoded.toString()
        }})
        console.log('Default PUT FORM→JSON:', await response.text())
        expect([500, 501, 502, 503]).toContain(response.status())
        }})
        }})

// -------------------- 12. FORM → XML --------------------
test.describe('/pet - PUT FORM → XML', () => {{
        test('200 - Successful operation', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: formUrlEncoded.toString()
        }})
        const
        text = await response.text()
        console.log('200 PUT FORM→XML:', text)
        expect(response.status()).toBe(200)
        expect(text).toContain('<pet>')
        }})

        test('400 - Invalid ID supplied', async ({{request}}) = > {{
          const
        form = new
        URLSearchParams({{wrong: 'data'}})
        const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: form.toString()
        }})
        console.log('400 PUT FORM→XML:', await response.text())
        expect(response.status()).toBe(400)
        }})

        test('404 - Pet not found', async ({{request}}) = > {{
          const
        form = new
        URLSearchParams({{id: '99999999', name: 'Ghost', photoUrls: 'url'}})
        const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: form.toString()
        }})
        console.log('404 PUT FORM→XML:', await response.text())
        expect(response.status()).toBe(404)
        }})

        test('422 - Validation exception', async ({{request}}) = > {{
          const
        form = new
        URLSearchParams({{name: '', photoUrls: ''}})
        const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/x-www-form-urlencoded'
          }},
          data: form.toString()
        }})
        console.log('422 PUT FORM→XML:', await response.text())
        expect(response.status()).toBe(422)
        }})

        test('default - Unexpected error', async ({{request}}) = > {{
          const
        response = await request.put('/pet', {{
          headers: {{
            'Accept': 'application/xml',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Force-Error': 'true'
          }},
          data: formUrlEncoded.toString()
        }})
        console.log('Default PUT FORM→XML:', await response.text())
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

                # content = getattr(response, "content", response)
                # clean_json = extract_and_sanitize_json(content)
                # parsed_dict = json.loads(clean_json)

                with open(self.output_dir / f"{file.stem}.spec.js", "w", encoding="utf-8") as f:
                    f.write(response.content)
                clean_code_fences(self.output_dir)

                print(f"✅ Saved LLM response for {file.name}")

            except Exception as e:
                print(f"❌ Failed to process {file.name}: {e}")



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
