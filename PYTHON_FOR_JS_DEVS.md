# Python for JavaScript Developers 🐍 ↔️ 📜

A quick reference guide for JavaScript/TypeScript developers learning Python.

## 🎯 Quick Comparison

| Feature | JavaScript/TypeScript | Python |
|---------|----------------------|--------|
| **Variables** | `const x = 5;` `let y = 10;` | `x = 5` `y = 10` |
| **Functions** | `function greet(name) {}` | `def greet(name):` |
| **Arrow Functions** | `const add = (a, b) => a + b` | `add = lambda a, b: a + b` |
| **Classes** | `class User {}` | `class User:` |
| **Imports** | `import { x } from 'module'` | `from module import x` |
| **Async** | `async function f() {}` | `async def f():` |
| **Null** | `null` / `undefined` | `None` |
| **Boolean** | `true` / `false` | `True` / `False` |
| **Comments** | `// comment` `/* block */` | `# comment` `'''block'''` |

## 📚 Detailed Examples

### 1. Variables & Types

**JavaScript:**
```javascript
// Declarations
const name = "John";           // Cannot reassign
let age = 30;                  // Can reassign
var old = "avoid";             // Old way

// Types (TypeScript)
const name: string = "John";
const age: number = 30;
const isActive: boolean = true;
const items: string[] = ["a", "b"];
const user: { name: string } = { name: "John" };
```

**Python:**
```python
# No const/let/var - just assign
name = "John"                  # Can reassign
age = 30

# Type hints (Python 3.5+)
name: str = "John"
age: int = 30
is_active: bool = True
items: list[str] = ["a", "b"]
user: dict = {"name": "John"}

# Multiple assignment
x, y, z = 1, 2, 3
```

### 2. Functions

**JavaScript:**
```javascript
// Regular function
function greet(name) {
    return `Hello ${name}`;
}

// Arrow function
const greet = (name) => `Hello ${name}`;

// With types (TypeScript)
function greet(name: string): string {
    return `Hello ${name}`;
}

// Default parameters
function greet(name = "World") {
    return `Hello ${name}`;
}

// Async function
async function fetchData() {
    const response = await fetch(url);
    return response.json();
}
```

**Python:**
```python
# Regular function
def greet(name):
    return f"Hello {name}"

# Lambda (like arrow function, but limited)
greet = lambda name: f"Hello {name}"

# With type hints
def greet(name: str) -> str:
    return f"Hello {name}"

# Default parameters
def greet(name="World"):
    return f"Hello {name}"

# Async function
async def fetch_data():
    response = await fetch(url)
    return response.json()
```

**Key Differences:**
- Python uses `:` and indentation instead of `{}`
- No parentheses needed for `return`
- `f"string"` is like JavaScript's template literals
- Python lambda is limited to single expressions

### 3. Classes

**JavaScript:**
```javascript
class User {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }
    
    greet() {
        return `Hello, I'm ${this.name}`;
    }
    
    static create(name, age) {
        return new User(name, age);
    }
}

// Usage
const user = new User("John", 30);
user.greet();
```

**Python:**
```python
class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def greet(self):
        return f"Hello, I'm {self.name}"
    
    @staticmethod
    def create(name, age):
        return User(name, age)

# Usage
user = User("John", 30)
user.greet()
```

**Key Differences:**
- `__init__` is like `constructor`
- `self` is like `this` (but must be explicit in parameters!)
- `@staticmethod` decorator instead of `static` keyword
- No `new` keyword needed

### 4. Arrays/Lists

**JavaScript:**
```javascript
// Arrays
const fruits = ["apple", "banana", "orange"];

// Common operations
fruits.push("grape");              // Add to end
fruits.pop();                      // Remove from end
fruits.length;                     // Get length
fruits[0];                         // Access by index
fruits.slice(0, 2);               // Get subset
fruits.includes("apple");         // Check existence

// Array methods
fruits.map(f => f.toUpperCase());
fruits.filter(f => f.length > 5);
fruits.forEach(f => console.log(f));

// Destructuring
const [first, second] = fruits;
```

**Python:**
```python
# Lists
fruits = ["apple", "banana", "orange"]

# Common operations
fruits.append("grape")             # Add to end
fruits.pop()                       # Remove from end
len(fruits)                        # Get length
fruits[0]                          # Access by index
fruits[0:2]                        # Get subset (slice)
"apple" in fruits                  # Check existence

# List comprehensions (powerful!)
[f.upper() for f in fruits]
[f for f in fruits if len(f) > 5]
for f in fruits: print(f)

# Unpacking
first, second, *rest = fruits
```

**Key Differences:**
- `append()` instead of `push()`
- `len()` is a function, not a property
- Slicing with `[start:end]` instead of `.slice()`
- List comprehensions are more powerful than `.map()` and `.filter()`

### 5. Objects/Dictionaries

**JavaScript:**
```javascript
// Objects
const user = {
    name: "John",
    age: 30,
    email: "john@example.com"
};

// Access
user.name;
user["name"];

// Add/modify
user.country = "USA";

// Check key exists
"name" in user;
user.hasOwnProperty("name");

// Get keys/values
Object.keys(user);
Object.values(user);
Object.entries(user);

// Destructuring
const { name, age } = user;

// Spread operator
const newUser = { ...user, age: 31 };
```

**Python:**
```python
# Dictionaries
user = {
    "name": "John",
    "age": 30,
    "email": "john@example.com"
}

# Access
user["name"]                       # Dot notation doesn't work!
user.get("name")                   # Safe access

# Add/modify
user["country"] = "USA"

# Check key exists
"name" in user

# Get keys/values
user.keys()
user.values()
user.items()

# Unpacking
name = user["name"]
age = user["age"]

# Merge dictionaries
new_user = {**user, "age": 31}
```

**Key Differences:**
- Must use bracket notation: `user["name"]` not `user.name`
- `.get()` method returns `None` if key doesn't exist (safer)
- `**dict` is like JavaScript's `...object` spread

### 6. Control Flow

**JavaScript:**
```javascript
// If statements
if (age >= 18) {
    console.log("Adult");
} else if (age >= 13) {
    console.log("Teen");
} else {
    console.log("Child");
}

// Ternary
const status = age >= 18 ? "Adult" : "Minor";

// Switch (no Python equivalent!)
switch (day) {
    case "Monday":
        console.log("Start of week");
        break;
    case "Friday":
        console.log("End of week");
        break;
    default:
        console.log("Midweek");
}

// For loops
for (let i = 0; i < 10; i++) {
    console.log(i);
}

for (const item of items) {
    console.log(item);
}

// While
while (condition) {
    // code
}
```

**Python:**
```python
# If statements (no parentheses, no braces!)
if age >= 18:
    print("Adult")
elif age >= 13:
    print("Teen")
else:
    print("Child")

# Ternary (different syntax)
status = "Adult" if age >= 18 else "Minor"

# Match-case (Python 3.10+, like switch)
match day:
    case "Monday":
        print("Start of week")
    case "Friday":
        print("End of week")
    case _:
        print("Midweek")

# For loops
for i in range(10):
    print(i)

for item in items:
    print(item)

# While
while condition:
    # code
```

**Key Differences:**
- Python uses indentation instead of `{}`
- `elif` instead of `else if`
- No parentheses needed for conditions
- `range(10)` generates 0-9
- No `break` needed in `match` (Python 3.10+)

### 7. Async/Await

**JavaScript:**
```javascript
// Promise
const fetchUser = () => {
    return fetch('/api/user')
        .then(res => res.json())
        .catch(err => console.error(err));
};

// Async/await
const fetchUser = async () => {
    try {
        const response = await fetch('/api/user');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(error);
    }
};

// Multiple parallel requests
const [users, posts] = await Promise.all([
    fetchUsers(),
    fetchPosts()
]);
```

**Python:**
```python
# Coroutine (like Promise)
async def fetch_user():
    response = await fetch('/api/user')
    return await response.json()

# Try/except (like try/catch)
async def fetch_user():
    try:
        response = await fetch('/api/user')
        data = await response.json()
        return data
    except Exception as error:
        print(error)

# Multiple parallel requests
import asyncio
users, posts = await asyncio.gather(
    fetch_users(),
    fetch_posts()
)
```

**Key Differences:**
- Very similar syntax!
- `except` instead of `catch`
- `asyncio.gather()` instead of `Promise.all()`
- Need `import asyncio` for utilities

### 8. Modules & Imports

**JavaScript:**
```javascript
// Export (ES6 modules)
export const name = "John";
export function greet() {}
export default class User {}

// Import
import User from './user';
import { name, greet } from './utils';
import * as utils from './utils';

// CommonJS (Node.js)
module.exports = { name, greet };
const { name, greet } = require('./utils');
```

**Python:**
```python
# In utils.py
name = "John"
def greet(): pass
class User: pass

# Import
from utils import User
from utils import name, greet
import utils

# Access
utils.name
utils.greet()
```

**Key Differences:**
- No `export` keyword - everything is exportable by default
- `from module import x` instead of `import { x } from 'module'`
- `import module` imports the whole module

### 9. Error Handling

**JavaScript:**
```javascript
try {
    throw new Error("Something went wrong");
} catch (error) {
    console.error(error.message);
} finally {
    console.log("Cleanup");
}

// Custom error
class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = "ValidationError";
    }
}
```

**Python:**
```python
try:
    raise Exception("Something went wrong")
except Exception as error:
    print(error)
finally:
    print("Cleanup")

# Custom error
class ValidationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)
```

**Key Differences:**
- `except` instead of `catch`
- `raise` instead of `throw`
- `as` for error variable binding

### 10. String Operations

**JavaScript:**
```javascript
// Template literals
const name = "John";
const greeting = `Hello ${name}!`;

// Methods
"hello".toUpperCase();
"HELLO".toLowerCase();
"  hello  ".trim();
"hello world".split(" ");
"hello".includes("ell");
"hello".startsWith("he");
"hello".replace("l", "L");
```

**Python:**
```python
# F-strings (Python 3.6+)
name = "John"
greeting = f"Hello {name}!"

# Methods
"hello".upper()
"HELLO".lower()
"  hello  ".strip()
"hello world".split(" ")
"ell" in "hello"
"hello".startswith("he")
"hello".replace("l", "L")
```

## 🎯 FastAPI ↔️ NestJS Comparison

### Route Definition

**NestJS:**
```typescript
@Controller('users')
export class UsersController {
    @Get()
    findAll(): User[] {
        return this.usersService.findAll();
    }
    
    @Post()
    create(@Body() createUserDto: CreateUserDto) {
        return this.usersService.create(createUserDto);
    }
    
    @Get(':id')
    findOne(@Param('id') id: string) {
        return this.usersService.findOne(id);
    }
}
```

**FastAPI:**
```python
from fastapi import APIRouter, Body

router = APIRouter()

@router.get("/users")
async def find_all() -> list[User]:
    return users_service.find_all()

@router.post("/users")
async def create(user: CreateUserDto = Body(...)):
    return users_service.create(user)

@router.get("/users/{id}")
async def find_one(id: str):
    return users_service.find_one(id)
```

### Dependency Injection

**NestJS:**
```typescript
@Injectable()
export class UsersService {
    constructor(
        private readonly db: DatabaseService,
        private readonly logger: LoggerService
    ) {}
}
```

**FastAPI:**
```python
from fastapi import Depends

# Define dependencies
def get_db():
    return DatabaseService()

def get_logger():
    return LoggerService()

# Use in endpoint
@router.get("/users")
async def get_users(
    db: DatabaseService = Depends(get_db),
    logger: LoggerService = Depends(get_logger)
):
    return db.query()
```

## 🚀 Quick Tips

1. **Indentation Matters**: Python uses indentation instead of `{}`
   ```python
   # GOOD
   if True:
       print("yes")
   
   # BAD
   if True:
   print("yes")  # IndentationError!
   ```

2. **No Semicolons**: They're optional (and unused)
   ```python
   x = 5       # Good
   y = 10;     # Also works but don't do it
   ```

3. **Naming Conventions**:
   - JavaScript: `camelCase` for variables/functions
   - Python: `snake_case` for variables/functions, `PascalCase` for classes

4. **List/Dict Comprehensions**: Super powerful!
   ```python
   # Instead of:
   squares = []
   for i in range(10):
       squares.append(i**2)
   
   # Do this:
   squares = [i**2 for i in range(10)]
   ```

5. **None vs null**: `None` is Python's `null`/`undefined`
   ```python
   value = None
   if value is None:  # Use 'is', not '=='
       print("No value")
   ```

Happy coding! 🎉

