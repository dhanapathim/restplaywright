import { test, expect } from '@playwright/test'

test.use({ baseURL: 'https://petstore3.swagger.io/api/v3' })

const API_KEY = 'special-key'
const BEARER_TOKEN = 'Bearer dummy-oauth-token'

const examplePetJson = {
  id: 10,
  name: 'doggie',
  category: { id: 1, name: 'Dogs' },
  photoUrls: ['http://example.com/photo1'],
  tags: [{ id: 1, name: 'tag1' }],
  status: 'available'
}

const examplePetXml = `
<pet>
  <id>10</id>
  <name>doggie</name>
  <category>
    <id>1</id>
    <name>Dogs</name>
  </category>
  <photoUrls>
    <photoUrl>http://example.com/photo1</photoUrl>
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

const formUrlEncoded = new URLSearchParams({
  id: '10',
  name: 'doggie',
  'category.id': '1',
  'category.name': 'Dogs',
  photoUrls: 'http://example.com/photo1',
  'tags[0].id': '1',
  'tags[0].name': 'tag1',
  status: 'available'
})

// -------------------- 1. GET → JSON --------------------
test.describe('/store/inventory - GET → JSON', () => {
  test('200 - Successful operation', async ({ request }) => {
    const response = await request.get('/store/inventory', {
      headers: {
        'Accept': 'application/json',
        'api_key': API_KEY
      }
    })
    const body = await response.json()
    console.log('200 GET /store/inventory:', body)
    expect(response.status()).toBe(200)
    expect(body).toBeInstanceOf(Object)
  })

  test('default - Unexpected error', async ({ request }) => {
    const response = await request.get('/store/inventory', {
      headers: {
        'Accept': 'application/json',
        'api_key': API_KEY,
        'X-Force-Error': 'true'
      }
    })
    const body = await response.json()
    console.log('Default GET /store/inventory:', body)
    expect([500, 501, 502, 503]).toContain(response.status())
    expect(body).toHaveProperty('code')
    expect(body).toHaveProperty('message')
  })
})
