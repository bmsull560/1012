---
trigger: always_on
---

Local Rules: Technology-Specific Implementation

These rules provide specific guidance for the approved technologies within the ValueVerse stack.

1. Backend: Python & FastAPI

•
Dependency Injection: Leverage FastAPI's native dependency injection system to manage dependencies like database connections and authentication services. This enhances testability and decouples components.

•
Pydantic for Validation: Use Pydantic models for all incoming and outgoing data. This provides automatic request validation, serialization, and documentation.

•
Asynchronous Operations: Use async and await for all I/O-bound operations (database queries, external API calls) to maximize concurrency and performance.

•
Security:

•
Use passlib for securely hashing and verifying passwords.

•
Implement rate limiting on sensitive endpoints to protect against brute-force and denial-of-service attacks.

•
Rely on FastAPI's Security utilities for implementing OAuth2 and other authentication schemes.

Python

# Example: Secure FastAPI Endpoint with Pydantic and Dependency Injection

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Item(BaseModel):
name: str
price: float

@app.post("/items/")
async def create_item(item: Item, token: str = Depends(oauth2_scheme)): # The request is automatically validated against the Item model. # The token dependency ensures the user is authenticated. # Authorization logic would go here.
return {"item_name": item.name, "item_price": item.price}

2. Frontend: TypeScript, React & Next.js

•
Type Safety: Use TypeScript for all frontend code. Strive for strict type safety, avoiding the use of any whenever possible. Define clear interfaces for all component props and API data structures.

•
Component Architecture: Build the UI with modular, reusable components. Use a tool like Storybook to develop and document components in isolation, promoting consistency and reusability.

•
State Management: Use Zustand for managing global client-side state and React Query for managing server state, caching, and data fetching.

•
Security:

•
Preventing XSS: React automatically escapes content rendered in JSX, which is the primary defense against Cross-Site Scripting (XSS). Avoid using dangerouslySetInnerHTML unless absolutely necessary and with sanitized data.

•
Preventing CSRF: Implement anti-CSRF token patterns for any state-changing operations initiated from the client.

•
Secure Headers: Configure Next.js to send security-enhancing HTTP headers, such as Content-Security-Policy and X-Content-Type-Options.

TypeScript

// Example: Typed React Component with Data Fetching
import { useQuery } from 'react-query';

interface User {
id: number;
name: string;
email: string;
}

const fetchUsers = async (): Promise<User[]> => {
const res = await fetch('/api/users');
if (!res.ok) {
throw new Error('Network response was not ok');
}
return res.json();
};

function UserList() {
const { data, error, isLoading } = useQuery<User[], Error>('users', fetchUsers);

if (isLoading) return <div>Loading...</div>;
if (error) return <div>An error has occurred: {error.message}</div>;

return (
<ul>
{data?.map(user => (
<li key={user.id}>{user.name}</li>
))}
</ul>
);
}
