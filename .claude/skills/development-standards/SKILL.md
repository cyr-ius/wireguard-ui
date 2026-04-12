---
name: development-standards
description: Normes de développement frontend et backend pour la mise en oeuvre de projet Angular/Fastapi
---

## When to Use This Skill

- Creation of new projects
- Code implementation
- Development of high-performance web services and microservices
- Creation of asynchronous applications
- Implementation of structured and tested API projects

# 🎓 Portalcrane Development Standards

## Framework Technologies

| Layer              | Technology      | Version     | Features                                    |
| ------------------ | --------------- | ----------- | ------------------------------------------- |
| **Frontend**       | Angular         | 21          | Signals, Signal Forms, Zoneless, Standalone |
| **Backend**        | FastAPI         | 0.135.1     | Async/Await, Pydantic v2                    |
| **UI Framework**   | Bootstrap       | 5.3.8       | Responsive, Accessible                      |
| **Icons**          | Bootstrap Icons | 1.13.1      | SVG Icons                                   |
| **Python Runtime** | Python          | 3.14        | Asynchronous                                |
| **Node Runtime**   | Node.js         | 18+         | ES2021                                      |
| **Deployment**     | Docker          | Multi-stage | Single Container SPA                        |
| **Database**       | SQLite          | Multi-stage | SQLModel, SQLAlchemy, Alembic               |

---

## 📘 ANGULAR 21 STANDARDS

### 0. Configuration Zoneless (Performance)

**Angular 21 apporte le mode zoneless pour performances optimales:**

Le mode zoneless désactive NgZone d'Angular et s'appuie sur les signaux pour la détection de changements.

```typescript
// src/main.ts - Application bootstrap
import { bootstrapApplication } from "@angular/platform-browser";
import { AppComponent } from "./app/app.component";
import { appConfig } from "./app/app.config";

bootstrapApplication(AppComponent, appConfig);
```

```typescript
// src/app/app.config.ts - Application configuration
import { ApplicationConfig, provideZoneChangeDetection } from "@angular/core";
import { provideRouter } from "@angular/router";
import { provideHttpClient } from "@angular/common/http";

export const appConfig: ApplicationConfig = {
  providers: [
    // ✅ Enable zoneless mode for better performance
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(),
  ],
};
```

**Avantages du mode zoneless:**

- ✅ Meilleures performances (pas de zone.js)
- ✅ Bundle plus petit
- ✅ Réactivité granulaire avec signaux
- ✅ Moins de changeDetection cycles

### 1. Principes Fondamentaux

**Angular 21 apporte des changements majeurs:**

- ✅ **Signaux** (réactivité granulaire)
- ✅ **Signal Forms** (formulaires réactifs simplifiés)
- ✅ **Zoneless** (sans NgZone, performances meilleures)
- ✅ **Standalone Components** (pas de modules)
- ❌ **Directives avec `*`** (dépréciées: `*ngIf`, `*ngFor`, `*ngSwitch`)
- ✅ **Control Flow** (syntaxe nouvelle: `@if`, `@for`, `@switch`)

### 2. Types de Composants

Tous les composants **doivent avoir des fichiers séparés** pour template et style:

```
app/features/user/
├── user-list/
│   ├── user-list.component.ts      ← Code TypeScript
│   ├── user-list.component.html    ← Template HTML
│   └── user-list.component.css     ← Styles CSS
```

#### Structure de Composant (Standalone)

```typescript
import { Component, input, output, OnInit, inject } from "@angular/core";
import { CommonModule } from "@angular/common";
import { signal, computed, effect } from "@angular/core";
import {
  email,
  form,
  FormField,
  required,
  submit,
} from "@angular/forms/signals";

// Standalone component - no module needed
@Component({
  selector: "app-user-profile",
  imports: [CommonModule, FormField],
  templateUrl: "./user-profile.component.html",
  styleUrl: "./user-profile.component.css",
})
export class UserProfileComponent implements OnInit {
  // Injected services
  private userService = inject(UserService);

  // Input signal (receives data from parent)
  userId = input<number>(0);

  // Output signal (sends data to parent)
  userSaved = output<User>();

  // Error signal
  readonly error = signal("");

  // Internal state using signals
  user = signal<User | null>(null);
  isLoading = signal(false);
  errorMessage = signal<string | null>(null);

  // Computed derived state (automatically updates)
  displayName = computed(() => {
    const usr = this.user();
    return usr ? `${usr.firstName} ${usr.lastName}` : "Unknown";
  });

  // Signal Forms
  private readonly userInit = { email: "", phone: "" };
  userModel = signal({ ...this.userInit });

  userForm = form(this.userModel, (schemaPath) => {
    required(schemaPath.email);
    required(schemaPath.phone);
    email(schemaPath.email);
  });

  constructor() {
    // Load user when userId input changes
    effect(() => {
      const id = this.userId();
      if (id > 0) {
        this.loadUser(id);
      }
    });
  }

  private async loadUser(id: number): Promise<void> {
    this.isLoading.set(true);
    try {
      const userData = await this.userService.getUser(id).toPromise();
      this.user.set(userData);
    } catch (error) {
      this.errorMessage.set("Failed to load user");
    } finally {
      this.isLoading.set(false);
    }
  }

  onSubmit(event: Event): void {
    event.preventDefault();

    sumibt(this.userForm, async (f) => {
      const formData = f().value();
      try {
        this.userSaved.emit(formData);
      } catch (err: unknown) {
        const httpErr = err as { error?: { detail?: string } };
        this.error.set(httpErr.error?.detail ?? "Authentication failed");
      }
    });
  }
}
```

### 3. Nouvelles Directives de Contrôle de Flux

**❌ ANCIEN (Déprécié):**

```html
<!-- Old directive syntax - DO NOT USE -->
<div *ngIf="isVisible">Content</div>
<div *ngFor="let item of items">{{ item }}</div>
<div *ngSwitch="status">
  <div *ngSwitchCase="'active'">Active</div>
</div>
```

**✅ NOUVEAU (Angular 21):**

```html
<!-- New control flow syntax - USE THIS -->
<!-- If statement -->
@if (isVisible) {
<div>Content</div>
} @else if (isLoading) {
<p>Loading...</p>
} @else {
<p>Hidden</p>
}

<!-- For loop -->
@for (item of items; track item.id) {
<div>{{ item.name }}</div>
}

<!-- Alternative: trackBy with function -->
@for (item of items; track trackByUserId($index, item)) {
<div>{{ item.name }}</div>
}

<!-- Switch statement -->
@switch (status) { @case ('active') {
<span class="badge bg-success">Active</span>
} @case ('inactive') {
<span class="badge bg-secondary">Inactive</span>
} @default {
<span class="badge bg-warning">Unknown</span>
} }

<!-- Empty state handling -->
@if (items.length > 0) {
<ul>
  @for (item of items; track item.id) {
  <li>{{ item.name }}</li>
  }
</ul>
} @else {
<p class="text-muted">No items found</p>
}
```

### 4. Signaux et Réactivité

Les signaux remplacent le système de zones d'Angular pour la détection de changements:

```typescript
import { signal, computed, effect } from "@angular/core";

export class ShoppingCartComponent {
  // Basic signal
  cartItems = signal<CartItem[]>([]);
  quantity = signal(0);
  discountPercent = signal(0);

  // Computed signal (derived state)
  subtotal = computed(() =>
    this.cartItems().reduce((sum, item) => sum + item.price * item.qty, 0),
  );

  discountAmount = computed(
    () => this.subtotal() * (this.discountPercent() / 100),
  );

  total = computed(() => this.subtotal() - this.discountAmount());

  constructor() {
    // Effect: runs whenever dependencies change
    effect(() => {
      const total = this.total();
      console.log(`Total changed to: $${total.toFixed(2)}`);
      this.logToAnalytics(total);
    });
  }

  // Modifying signals
  addItem(item: CartItem): void {
    // Update by creating new array (immutable pattern)
    this.cartItems.update((items) => [...items, item]);
    this.quantity.update((q) => q + 1);
  }

  removeItem(itemId: number): void {
    this.cartItems.update((items) => items.filter((i) => i.id !== itemId));
  }

  // Set values directly
  applyDiscount(percent: number): void {
    this.discountPercent.set(percent);
  }

  private logToAnalytics(total: number): void {
    // Log to analytics
  }
}
```

### 5. Signal Forms

Les Signal Forms simplifient la gestion des formulaires.
Le template doit être dans un fichier dédié, exception dans ce chaitre pour des raisons pratiques d'explications

```typescript
import { Component } from "@angular/core";
import {
  form,
  email,
  FormField,
  required,
  submit,
} from "@angular/forms/signals";

@Component({
  selector: "app-registration-form",
  standalone: true,
  imports: [FormRoot, FormField],
  template: `
    <form [formRoot]="registrationForm">
      <input [formField]="registrationForm.username" />
      @if (
        registrationForm.username().invalid() &&
        registrationForm.username().errors().length
      ) {
        <ul>
          @for (error of registrationForm.username().errors(); track error) {
            <li>{{ error.message }}</li>
          }
        </ul>
      }

      <input type="email" [formField]="registrationForm.email" />
      <input type="password" [formField]="registrationForm.password" />
      <input type="password" [formField]="registrationForm.confirmPassword" />
      <input type="checkbox" [formField]="registrationForm.acceptTerms" />
      <button type="submit">Register</button>
    </form>
  `,
})
export class RegistrationFormComponent {
  private readonly registrationInit = {
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false,
  };

  registrationModel = signal({ ...this.registrationInit });

  registrationForm = form(
    this.userModel,
    (schemaPath) => {
      required(schemaPath.username);
      required(schemaPath.email);
      required(schemaPath.password);
      required(schemaPath.confirmPassword);
      required(schemaPath.acceptTerms);
      email(schemaPath.email);
      validate(schemaPath.confirmPassword, ({ value, valueOf }) => {
        const confirmPassword = value();
        const password = valueOf(schemaPath.password);
        if (confirmPassword !== password) {
          return {
            kind: "passwordMismatch",
            message: "Passwords do not match",
          };
        }
      });
    },
    {
      submission: {
        action: async (f) => this.submitToServer(f),
      },
    },
  );

  private async submitToServer(f: form) {
    const formData = this.registrationForm().value();
    console.log("Form submitted:", formData);
    try {
      await firstValueFrom(this.registrationService.register(formData));
      this.registrationForm().reset({ ...this.registrationInit });
    } catch (error) {
      console.error("Error submitting form:", error);
    }
  }
}
```

### 6. Services et Injection de Dépendances

```typescript
import { Injectable, inject } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable, signal } from "@angular/core";
import { environment } from "../../../environments/environment";

interface User {
  id: number;
  username: string;
  email: string;
}

// Singleton service
@Injectable({
  providedIn: "root",
})
export class UserService {
  // Inject dependencies using inject()
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/users`;

  // State management using signals
  users = signal<User[]>([]);
  selectedUser = signal<User | null>(null);
  isLoading = signal(false);

  getUsers(): Observable<User[]> {
    this.isLoading.set(true);
    return new Observable((observer) => {
      this.http.get<User[]>(this.apiUrl).subscribe({
        next: (users) => {
          this.users.set(users);
          observer.next(users);
          observer.complete();
        },
        error: (error) => {
          this.isLoading.set(false);
          observer.error(error);
        },
        complete: () => this.isLoading.set(false),
      });
    });
  }

  getUser(id: number): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/${id}`);
  }

  createUser(user: Omit<User, "id">): Observable<User> {
    return this.http.post<User>(this.apiUrl, user);
  }

  updateUser(id: number, user: Partial<User>): Observable<User> {
    return this.http.put<User>(`${this.apiUrl}/${id}`, user);
  }

  deleteUser(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }
}
```

### 7. TemplateHTML Structure

**✅ Format recommandé avec fichier séparé:**

```html
<!-- user-list.component.html -->
<div class="container mt-5">
  <div class="row mb-4">
    <div class="col-md-6">
      <h1>
        <i class="bi bi-person-lines-fill"></i>
        Users
      </h1>
    </div>
    <div class="col-md-6 text-end">
      <button class="btn btn-primary" (click)="openCreateModal()">
        <i class="bi bi-plus-circle"></i>
        Add User
      </button>
    </div>
  </div>

  <!-- Search and filter -->
  <div class="row mb-3">
    <div class="col-md-6">
      <input
        type="text"
        class="form-control"
        placeholder="Search users..."
        (input)="filterUsers($event)"
      />
    </div>
  </div>

  <!-- Loading state -->
  @if (userService.isLoading()) {
  <div class="alert alert-info">
    <i class="bi bi-hourglass-split"></i>
    Loading users...
  </div>
  }

  <!-- Error state -->
  @if (errorMessage(); as error) {
  <div class="alert alert-danger alert-dismissible fade show" role="alert">
    <i class="bi bi-exclamation-triangle"></i>
    {{ error }}
    <button type="button" class="btn-close" (click)="clearError()"></button>
  </div>
  }

  <!-- Users table -->
  @if (filteredUsers().length > 0) {
  <div class="table-responsive">
    <table class="table table-striped table-hover">
      <thead class="table-light">
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Email</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        @for (user of filteredUsers(); track user.id) {
        <tr>
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>{{ user.email }}</td>
          <td>
            <button
              class="btn btn-sm btn-info"
              (click)="editUser(user)"
              title="Edit"
            >
              <i class="bi bi-pencil"></i>
            </button>
            <button
              class="btn btn-sm btn-danger"
              (click)="deleteUser(user.id)"
              title="Delete"
            >
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
        }
      </tbody>
    </table>
  </div>
  } @else {
  <div class="alert alert-warning text-center">
    <i class="bi bi-inbox"></i>
    No users found
  </div>
  }
</div>
```

### 8. CSS Styles Structure

**✅ Format avec fichier séparé:**

```css
/* user-list.component.css */

/* Container styling */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

/* Headings */
h1 {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  color: #212529;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Button styling */
.btn {
  transition: all 0.3s ease;
}

.btn-primary {
  background-color: #0d6efd;
}

.btn-primary:hover {
  background-color: #0b5ed7;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(13, 110, 253, 0.3);
}

/* Table styling */
.table-responsive {
  border-radius: 0.25rem;
  overflow: hidden;
}

.table {
  margin-bottom: 0;
}

.table thead {
  background-color: #f8f9fa;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.875rem;
}

.table tbody tr:hover {
  background-color: #f5f5f5;
}

/* Alerts */
.alert {
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Input fields */
input[type="text"],
input[type="email"],
textarea,
select {
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  padding: 0.5rem 0.75rem;
}

input:focus,
textarea:focus,
select:focus {
  border-color: #0d6efd;
  outline: none;
  box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

/* Icons from Bootstrap Icons */
.bi {
  display: inline-block;
  width: 1em;
  height: 1em;
  margin-right: 0.25rem;
}
```

### 9. Architecture des Dossiers

```
frontend/src/app/
├── core/                              # Singleton services, guards, interceptors
│   ├── services/
│   │   ├── auth.service.ts           # Authentication
│   │   ├── api.service.ts            # HTTP API calls
│   │   ├── theme.service.ts          # Theme management
│   │   └── ...
│   ├── guards/
│   │   └── auth.guard.ts             # Route protection
│   ├── interceptors/
│   │   └── auth.interceptor.ts       # Add JWT tokens
│   ├── models/
│   │   ├── auth.models.ts
│   │   ├── user.models.ts
│   │   └── ...
│   └── constants/
│       └── app.constants.ts
│
├── features/                          # Feature modules (lazy loaded)
│   ├── auth/
│   │   ├── login/
│   │   │   ├── login.component.ts
│   │   │   ├── login.component.html
│   │   │   └── login.component.css
│   │   └── ...
│   ├── dashboard/
│   │   ├── dashboard.component.ts
│   │   ├── dashboard.component.html
│   │   └── dashboard.component.css
│   └── ...
│
├── shared/                            # Reusable components, pipes, directives
│   ├── components/
│   │   ├── header/
│   │   ├── layout/
│   │   └── ...
│   ├── pipes/
│   │   └── custom.pipe.ts
│   └── directives/
│       └── custom.directive.ts
│
├── app.config.ts                     # Angular configuration
├── app.routes.ts                     # Route definitions
├── app.component.ts                  # Root component
└── main.ts                           # Application entry point
```

### 10. Routage

```typescript
// app.routes.ts
import { Routes, CanActivateFn } from "@angular/router";
import { inject } from "@angular/core";
import { AuthGuard } from "./core/guards/auth.guard";

// Define routes
export const routes: Routes = [
  {
    path: "",
    pathMatch: "full",
    redirectTo: "dashboard",
  },
  {
    path: "login",
    loadComponent: () =>
      import("./features/auth/login/login.component").then(
        (m) => m.LoginComponent,
      ),
  },
  {
    path: "dashboard",
    loadComponent: () =>
      import("./features/dashboard/dashboard.component").then(
        (m) => m.DashboardComponent,
      ),
    canActivate: [AuthGuard],
  },
  {
    path: "users",
    loadComponent: () =>
      import("./features/users/user-list/user-list.component").then(
        (m) => m.UserListComponent,
      ),
    canActivate: [AuthGuard],
  },
  {
    path: "**",
    redirectTo: "dashboard",
  },
];
```

---

## 🐍 FASTAPI STANDARDS

### 1. Structure de base

```python
"""
Portalcrane - Docker Registry Management Application
Main FastAPI entry point with async support.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown handler."""
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")


# FastAPI app with configuration
app = FastAPI(
    title="Portalcrane API",
    description="Docker Registry Management API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### 2. Modèles Pydantic

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

# Request model
class UserCreate(BaseModel):
    """User creation request model."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ...,
        min_length=8,
        description="Password must be at least 8 characters"
    )
    is_admin: bool = Field(default=False, description="Admin privileges")

    @validator('username')
    def username_alphanumeric(cls, v):
        """Validate username contains only alphanumeric and underscores."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric with underscores')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123",
                "is_admin": False
            }
        }


# Response model
class UserResponse(BaseModel):
    """User response model (excludes sensitive data)."""

    id: int
    username: str
    email: EmailStr
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Request/Response with nested models
class RegistryResponse(BaseModel):
    """Registry with nested images."""

    id: int
    name: str
    description: Optional[str] = None
    images: List[dict] = Field(default_factory=list)
```

### 3. Routes Asynchrones

```python
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])


# Dependency injection
async def get_db() -> AsyncSession:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# GET - Read all
@router.get("", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[UserResponse]:
    """
    Retrieve all users with pagination.

    - **skip**: Number of users to skip (default: 0)
    - **limit**: Maximum users to return (default: 100, max: 1000)
    """
    logger.info(f"Fetching users with skip={skip}, limit={limit}")

    try:
        users = await db.get_users(skip=skip, limit=limit)
        return users
    except Exception as exc:
        logger.error(f"Error fetching users: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


# GET - Read one
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Get user by ID.

    - **user_id**: The user's unique identifier
    """
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user


# POST - Create
@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Create a new user.

    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Strong password (min 8 characters)
    """
    logger.info(f"Creating user: {user_data.username}")

    # Check if user already exists
    existing_user = await db.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    try:
        new_user = await db.create_user(user_data)
        logger.info(f"User created: {new_user.id}")
        return new_user
    except Exception as exc:
        logger.error(f"Error creating user: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


# PUT - Update
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update an existing user.

    - **user_id**: The user's unique identifier
    - **user_update**: Fields to update
    """
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    try:
        updated_user = await db.update_user(user_id, user_update)
        return updated_user
    except Exception as exc:
        logger.error(f"Error updating user: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


# DELETE
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a user by ID.

    - **user_id**: The user's unique identifier
    """
    user = await db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    try:
        await db.delete_user(user_id)
        logger.info(f"User deleted: {user_id}")
    except Exception as exc:
        logger.error(f"Error deleting user: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
```

### 4. Services Asynchrones

```python
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class RegistryService:
    """
    Service for Docker registry operations.
    Handles all async registry-related logic.
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize service with database session."""
        self.db = db_session

    async def list_images(
        self,
        registry_id: int,
        limit: int = 100
    ) -> List[dict]:
        """
        List all images in a registry.

        Args:
            registry_id: Registry identifier
            limit: Maximum images to return

        Returns:
            List of image data

        Raises:
            ValueError: If registry not found
        """
        logger.info(f"Listing images for registry {registry_id}")

        registry = await self.db.get_registry(registry_id)
        if not registry:
            raise ValueError(f"Registry {registry_id} not found")

        images = await self.db.list_images(registry_id, limit=limit)
        return images

    async def get_image_metadata(
        self,
        registry_id: int,
        image_name: str
    ) -> dict:
        """
        Fetch detailed image metadata from registry.

        Args:
            registry_id: Registry identifier
            image_name: Full image name

        Returns:
            Image metadata

        Raises:
            ValueError: If image not found
        """
        logger.info(f"Fetching metadata for {image_name}")

        image = await self.db.get_image(registry_id, image_name)
        if not image:
            raise ValueError(f"Image {image_name} not found")

        # Fetch additional metadata asynchronously
        metadata = await self._fetch_remote_metadata(registry_id, image_name)
        return metadata

    async def _fetch_remote_metadata(
        self,
        registry_id: int,
        image_name: str
    ) -> dict:
        """Fetch metadata from remote registry."""
        # Implementation with async HTTP calls
        pass

    async def scan_image_cves(
        self,
        registry_id: int,
        image_name: str
    ) -> dict:
        """
        Scan image for CVE vulnerabilities.

        Args:
            registry_id: Registry identifier
            image_name: Full image name

        Returns:
            Scan results with vulnerability data

        Raises:
            RuntimeError: If scan fails
        """
        logger.info(f"Scanning {image_name} for CVEs")

        try:
            scan_result = await self._run_trivy_scan(registry_id, image_name)
            await self.db.save_scan_result(image_name, scan_result)
            return scan_result
        except Exception as exc:
            logger.error(f"CVE scan failed: {exc}")
            raise RuntimeError("Failed to scan image for vulnerabilities")

    async def _run_trivy_scan(
        self,
        registry_id: int,
        image_name: str
    ) -> dict:
        """Execute Trivy vulnerability scan."""
        # Implementation with subprocess or API call
        pass
```

### 5. Gestion Configuration (Variables d'environnement)

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings from environment variables.
    Loaded from .env file and container environment.
    """

    # App settings
    app_title: str = "Portalcrane"
    app_version: str = "1.0.0"
    debug: bool = False

    # Security
    secret_key: str  # MUST be set in production
    admin_username: str = "admin"
    admin_password: str = "changeme"

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "portalcrane"
    db_user: str = "postgres"
    db_password: str = "password"

    # Registry
    registry_url: str = "http://localhost:5000"
    registry_username: Optional[str] = None
    registry_password: Optional[str] = None

    # Docker Hub (for staging)
    dockerhub_username: Optional[str] = None
    dockerhub_token: Optional[str] = None

    # Vulnerability scanning
    vuln_scan_enabled: bool = True
    vuln_scan_severities: str = "CRITICAL,HIGH"
    vuln_scan_timeout: int = 300

    # Logging
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "*"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """Construct database connection URL."""
        return (
            f"postgresql+asyncpg://"
            f"{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origins_list(self) -> list:
        """Parse CORS origins from string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Singleton instance
settings = Settings()
```

**Fichier `.env` pour conteneur:**

```bash
# .env
APP_TITLE=Portalcrane
DEBUG=false

# Security - MUST be changed in production!
SECRET_KEY=change-this-secret-key-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme

# Database
DB_HOST=db
DB_PORT=5432
DB_NAME=portalcrane
DB_USER=postgres
DB_PASSWORD=postgres_password

# Registry
REGISTRY_URL=http://localhost:5000
REGISTRY_USERNAME=
REGISTRY_PASSWORD=

# Vulnerability scanning
VULN_SCAN_ENABLED=true
VULN_SCAN_SEVERITIES=CRITICAL,HIGH
VULN_SCAN_TIMEOUT=300

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=*
```

### 6. Exception Handling

```python
from fastapi import HTTPException, status
from typing import Optional

class BaseAPIException(Exception):
    """Base class for API exceptions."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[dict] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers


class NotFoundException(BaseAPIException):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with ID {resource_id} not found"
        )


class ConflictException(BaseAPIException):
    """Resource already exists."""

    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )


class UnauthorizedException(BaseAPIException):
    """Authentication failed."""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(BaseAPIException):
    """Authorization failed."""

    def __init__(self, detail: str = "Access forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


# Exception handlers
@app.exception_handler(NotFoundException)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(ConflictException)
async def conflict_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
```

---

## 🏗️ ARCHITECTURE CONTENEUR

L'application entière est déployée dans un **seul conteneur Docker**:

```dockerfile
# Dockerfile (Multi-stage build)

# Stage 1: Build frontend
FROM node:18-alpine as frontend_builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build -- --configuration production

# Stage 2: Build backend
FROM python:3.14-slim as backend_builder
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Runtime
FROM python:3.14-slim
WORKDIR /app

# Copy built frontend
COPY --from=frontend_builder /app/frontend/dist ./frontend/dist

# Copy backend
COPY --from=backend_builder /app/backend /app/backend
COPY backend/ /app/backend/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/api/health')"

# Expose port
EXPOSE 8080

# Run FastAPI app serving static frontend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Variables d'environnement du conteneur:**

```bash
# Variables d'environnement transmises au conteneur

# Authentification
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key_min_32_chars

# Registre
REGISTRY_URL=http://registry:5000
REGISTRY_USERNAME=
REGISTRY_PASSWORD=

# Scan de vulnérabilités
VULN_SCAN_ENABLED=true
VULN_SCAN_SEVERITIES=CRITICAL,HIGH

# Logging
LOG_LEVEL=INFO
```

---

## 📋 CONVENTIONS COMMUNES

### 1. Noms de Fichiers

```
# Angular
my-component.component.ts       # Composant
my-component.component.html     # Template
my-component.component.css      # Styles
my.service.ts                   # Service
my.pipe.ts                      # Pipe
my.directive.ts                 # Directive
my.guard.ts                     # Guard

# FastAPI
user_service.py                 # Service
user_models.py                  # Modèles Pydantic
user_routes.py                  # Routes
config.py                       # Configuration
exceptions.py                   # Exceptions personnalisées
```

### 2. Conventions de Nommage

```typescript
// Angular/TypeScript
const MAX_RETRY = 3;                    // Constantes
let currentUser: User | null;           // Variables
function getUserById(id: number): User; // Fonctions
class UserService { }                   // Classes
interface IUser { }                     // Interfaces
type AuthResponse = { ... };            // Types
enum Status { ACTIVE, INACTIVE }        // Énumérations

// HTML templates
data-testid="user-form"                 // Tests
aria-label="Close modal"                // Accessibilité
(click)="handleClick()"                 // Événements
(keydown.enter)="submitForm()"          // Événements clavier
[attr.aria-expanded]="isOpen()"         // Attributs dynamiques
```

```python
# Python/FastAPI
MAX_RETRIES = 3                         # Constantes
current_user = None                     # Variables
def get_user_by_id(user_id: int):      # Fonctions
class UserService:                      # Classes
async def fetch_data():                 # Fonctions asynchrones
```

### 3. Gestion d'Erreurs

```typescript
// Angular - Error handling
try {
  const user = await this.userService.getUser(id).toPromise();
  this.selectedUser.set(user);
} catch (error) {
  logger.error("Failed to load user", error);
  this.errorMessage.set("Failed to load user. Please try again.");
}
```

```python
# FastAPI - Error handling
try:
    user = await self.db.get_user(user_id)
    if not user:
        raise NotFoundException("User", user_id)
    return user
except Exception as exc:
    logger.error(f"Error fetching user {user_id}: {exc}")
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )
```

---

## 🔧 PRE-COMMIT CONFIGURATION & LINTING

Tous les changements doivent respecter la configuration définie dans `.pre-commit-config.yaml`.

### Hooks Disponibles

Le fichier `.pre-commit-config.yaml` configure les outils suivants:

#### 1. **Ruff** - Python Linting & Formatting

Ruff remplace Black, Flake8, isort et autres (outils Python).

```bash
# Run all ruff checks/formatting
ruff check backend/ --fix        # Auto-fix linting issues
ruff format backend/             # Format code

# Configuration (pyproject.toml)
[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "C4", "UP"]
ignore = ["E501"]  # Line too long is handled by formatter
```

**Utilisé pour:**

- Vérification PEP 8
- Formatage du code Python
- Tri des imports
- Réduction de la complexité

#### 2. **Python Typing Update** - Type Hints Modernization

Met à jour la syntaxe des type hints Python aux standards modernes.

```bash
# Manual run (not automatic)
pre-commit run --hook-stage manual python-typing-update --all-files

# Configuration
# Python 3.14+ syntax: `str | None` au lieu de `Optional[str]`
# `list[int]` au lieu de `List[int]`
```

**Exemples de mise à jour:**

```python
# Before (old syntax)
from typing import Optional, List
def get_users() -> Optional[List[str]]:
    pass

# After (Python 3.14 syntax)
def get_users() -> list[str] | None:
    pass
```

#### 3. **Prettier** - Frontend Formatting

Formate HTML, JSON, YAML, et Markdown.

```bash
# Format frontend files
npm run prettier
cd frontend && npx prettier --write "src/**/*.{ts,html,scss}"

# Configuration (.prettierrc)
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "arrowParens": "avoid"
}
```

#### 4. **Codespell** - Spell Checking

Vérifie l'orthographe et détecte les erreurs courantes.

```bash
# Check spelling in all files
codespell

# Auto-fix spelling errors
codespell --write-changes

# Configuration (.codespellrc)
skip = ./.git,*.json,*.csv,.devcontainer,.vscode
ignore-words-list = te
```

#### 5. **Standard Pre-commit Hooks**

Hooks fournis par pre-commit pour validations basiques:

```bash
# Standard validations applied automatically
check-json           # Validate JSON files
check-yaml          # Validate YAML files (with --unsafe)
check-toml          # Validate TOML files
check-added-large-files  # Prevent committing large files
end-of-file-fixer   # Ensure files end with newline
trailing-whitespace # Remove trailing spaces
mixed-line-ending   # Normalize line endings
```

Assurez-vous que les fichiers se terminent par un saut de ligne.
Supprimez les espaces de fin de ligne.
Normalisez les fins de ligne.

#### 6. **yamllint** - YAML Validation

Valide la structure YAML selon les standards.

```bash
# Check YAML files
yamllint .

# Configuration (.yamllint)
extends: default
rules:
  line-length: disable
  indentation:
    spaces: 2
```

### Exécution Manuelle des Hooks

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff-format --all-files
pre-commit run prettier --all-files

# Install pre-commit hook (auto-run on git commit)
pre-commit install

# Update hooks to latest versions
pre-commit autoupdate

# Disable hooks for single commit (not recommended!)
git commit --no-verify
```

### Workflow Recommandé

**Avant chaque commit:**

```bash
# 1. Format all code
cd backend && ruff format . && cd ..
cd frontend && npm run prettier && cd ..

# 2. Run all pre-commit hooks
pre-commit run --all-files

# 3. Fix any remaining issues manually
# (ruff might have unfixable errors)

# 4. Verify no errors remain
pre-commit run --all-files  # Should pass without changes

# 5. Run tests
cd backend && python -m pytest && cd ..
cd frontend && npm run test && cd ..

# 6. Commit changes
git add .
git commit -m "feat(scope): description"
```

### Configuration IDE pour Auto-Format

**VS Code - `.vscode/settings.json`:**

```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  },
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[html]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[yaml]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### Erreurs Courantes et Fixes

**Erreur: "Line too long"**

```python
# ❌ WRONG - Line > 100 chars
user_data = UserService.get_all_active_users_with_pending_transactions_and_notifications()

# ✅ CORRECT - Break into multiple lines
user_data = UserService.get_all_active_users_with_pending_transactions_and_notifications()
```

**Erreur: "Import sorting"**

```python
# ❌ WRONG - Wrong import order
import os
from typing import List
import sys
from app.models import User

# ✅ CORRECT - Group: stdlib, third-party, local
import os
import sys
from typing import List

from app.models import User
```

**Erreur: "Type hints missing"**

```python
# ❌ WRONG - No type hints
def process_data(data):
    return data.strip()

# ✅ CORRECT - Complete type hints
def process_data(data: str) -> str:
    """Process user input.

    Args:
        data: Input string to process.

    Returns:
        str: Processed string.
    """
    return data.strip()
```

---

## ⚠️ ERREURS COURANTES À ÉVITER

### Frontend - Angular

**❌ Utiliser les anciennes directives:**

```typescript
// WRONG - Deprecated directives
<div *ngIf="isVisible">Content</div>
<div *ngFor="let item of items">{{ item }}</div>
```

**✅ Utiliser le nouveau control flow:**

```typescript
// CORRECT - Use control flow
@if (isVisible) {
  <div>Content</div>
}

@for (item of items; track item.id) {
  <div>{{ item }}</div>
}
```

**❌ Ne pas utiliser les signaux:**

```typescript
// WRONG - Old way with property
export class MyComponent {
  isLoading = false; // Not reactive
  items: Item[] = []; // Not tracked
}
```

**✅ Utiliser les signaux:**

```typescript
// CORRECT - Reactive with signals
export class MyComponent {
  isLoading = signal(false); // Reactive state
  items = signal<Item[]>([]); // Tracked changes
  itemCount = computed(
    () =>
      // Derived state
      this.items().length,
  );
}
```

**❌ Inliner trop de code HTML/CSS:**

```typescript
// WRONG - 200 lignes de HTML inlinées
@Component({
  selector: 'app-complex',
  template: `<div>... 150 lignes ...</div>`,
  styles: [`... 100 lignes CSS ...`]
})
```

**✅ Utiliser des fichiers séparés:**

```typescript
// CORRECT - External files
@Component({
  selector: 'app-complex',
  templateUrl: './complex.component.html',
  styleUrls: ['./complex.component.scss']
})
```

**❌ Utiliser `any` type:**

```typescript
// WRONG - Lose type safety
function processData(data: any): any {
  return data.transform();
}
```

**✅ Utiliser des types spécifiques:**

```typescript
// CORRECT - Strong typing
interface DataModel {
  id: number;
  name: string;
}

function processData(data: DataModel): string {
  return data.name.toUpperCase();
}
```

**❌ Oublier de se désabonner (RxJS):**

```typescript
// WRONG - Memory leak
export class MyComponent implements OnInit {
  ngOnInit() {
    this.service.data$.subscribe((data) => {
      this.items = data;
    });
  }
}
```

**✅ Utiliser takeUntilDestroyed ou signaux:**

```typescript
// CORRECT - Proper cleanup
import { takeUntilDestroyed } from "@angular/core/rxjs-interop";

export class MyComponent {
  private destroyRef = inject(DestroyRef);

  constructor(private service: Service) {
    this.service.data$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((data) => {
        this.items = data;
      });
  }
}
```

### Backend - FastAPI

**❌ Backtrace dans le retour client**

```python
# WRONG - Information leak
try:
  function()
except Exception as exc:
  return f"Error {exc}"
```

**❌ Endpoints non-asynchrones:**

```python
# WRONG - Block thread
@app.get("/users")
def get_users():  # Not async!
    users = db.query(User).all()
    return users
```

**✅ Endpoints asynchrones:**

```python
# CORRECT - Async all the way
@app.get("/users")
async def get_users(
    db: AsyncSession = Depends(get_db)
) -> List[UserResponse]:
    """Get all users."""
    users = await db.get_all_users()
    return users
```

**❌ Utiliser print() pour logs:**

```python
# WRONG - No log levels, hard to grep
@app.get("/data")
async def get_data():
    print("User requested data")  # Bad!
    return {"status": "ok"}
```

**✅ Utiliser logging:**

```python
# CORRECT - Proper logging
import logging

logger = logging.getLogger(__name__)

@app.get("/data")
async def get_data() -> dict:
    """Get data."""
    logger.info("User requested data")
    return {"status": "ok"}
```

**❌ Pas de type hints:**

```python
# WRONG - No type safety
def create_user(user_data):
    return UserService.create(user_data)
```

**✅ Type hints complets:**

```python
# CORRECT - Full type hints
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Create new user.

    Args:
        user_data: User creation request.
        db: Database session.

    Returns:
        UserResponse: Created user.

    Raises:
        HTTPException: If user already exists.
    """
    user = await db.create_user(user_data)
    return user
```

**❌ Gestion d'erreurs manquante:**

```python
# WRONG - No error handling
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = await db.get_item(item_id)
    return item  # Crashes if not found!
```

**✅ Gestion d'erreurs appropriée:**

```python
# CORRECT - Proper error handling
@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db)
) -> ItemResponse:
    """Get item by ID.

    Args:
        item_id: Item unique ID.
        db: Database session.

    Returns:
        ItemResponse: Item data.

    Raises:
        HTTPException: If item not found.
    """
    item = await db.get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )
    return item
```

**❌ Hardcoder la configuration:**

```python
# WRONG - Secrets in code!
DATABASE_URL = "postgresql://user:password@localhost/db"
SECRET_KEY = "my-secret-key"
ADMIN_PASSWORD = "fixed-password"
```

**✅ Utiliser les variables d'environnement:**

```python
# CORRECT - Load from environment
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str  # From env
    secret_key: str    # From env
    admin_password: str  # From env

    class Config:
        env_file = ".env"

settings = Settings()
```

**❌ Pas de validation Pydantic:**

```python
# WRONG - No validation
@app.post("/users")
async def create_user(data: dict):
    # Anything goes!
    user = await db.create(data)
    return user
```

**✅ Validation avec Pydantic:**

```python
# CORRECT - Strong validation
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username 3-50 chars"
    )
    email: EmailStr  # Validates email format
    password: str = Field(
        ...,
        min_length=8,
        description="Password min 8 chars"
    )

@app.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Create user with validation."""
    # Only valid data reaches here
    user = await db.create_user(user_data)
    return user
```

---

## ✅ CHECKLIST AVANT COMMIT

**Pour les changements Angular:**

- [ ] Composants utilisant `@if`, `@for`, `@switch` (pas `*ngIf`, `*ngFor`, `*ngSwitch`)
- [ ] Templates dans fichier `.html` séparé
- [ ] Styles CSS dans fichier `.css` séparé
- [ ] Services utilisant `inject()` pour l'injection de dépendances
- [ ] État géré avec `signal()` et `computed()`
- [ ] Formulaires avec `Signal Forms`
- [ ] Pas d'imports circulaires
- [ ] Assurez-vous que les fichiers `.html` et `.css` se terminent par un saut de ligne.

**Pour les changements FastAPI:**

- [ ] Toutes les fonctions de route sont `async`
- [ ] Modèles Pydantic pour validation
- [ ] Gestion d'erreurs appropriée avec `HTTPException`
- [ ] Logging utilisé (pas `print()`)
- [ ] Type hints sur toutes les fonctions
- [ ] Docstrings complètes
- [ ] Variables d'environnement via `Settings`
- [ ] Assurez-vous que les fichiers `.py` se terminent par un saut de ligne.

---

**Pour la documentation:**

- [ ] Utiliser le standard markdown
- [ ] Suffixer les fichiers avec l'extension `.md`
- [ ] Assurez-vous que les fichiers se terminent par un saut de ligne.

---

## 🔗 Ressources Complètes

### Frontend - Angular 21

- [Angular 21 Official Docs](https://angular.dev/overview) - Documentation complète
- [Angular Signals Guide](https://angular.dev/guide/signals) - API Signaux
- [Angular Forms](https://angular.dev/guide/forms) - Forms réactives
- [Angular HttpClient](https://angular.dev/guide/http) - HTTP API
- [Angular Routing](https://angular.dev/guide/routing) - Routage
- [Control Flow Syntax](https://angular.dev/guide/control-flow) - @if, @for, @switch
- [Dependency Injection](https://angular.dev/guide/di) - Injection de dépendances
- [TypeScript Handbook](https://www.typescriptlang.org/docs/) - Langage TypeScript

### UI & Styling

- [Bootstrap 5.3 Documentation](https://getbootstrap.com/docs/5.3/) - Framework CSS
- [Bootstrap Icons Library](https://icons.getbootstrap.com/) - Icônes SVG
- [SCSS Documentation](https://sass-lang.com/documentation) - CSS préprocesseur
- [CSS Grid & Flexbox](https://developer.mozilla.org/en-US/docs/Web/CSS) - Mise en page

### Backend - FastAPI

- [FastAPI Official Documentation](https://fastapi.tiangolo.com/) - Documentation complète
- [Pydantic v2 Docs](https://docs.pydantic.dev/latest/) - Validation des données
- [Uvicorn Documentation](https://www.uvicorn.org/) - Serveur ASGI
- [Python Type Hints](https://docs.python.org/3/library/typing.html) - Système de types
- [Python Async/Await](https://docs.python.org/3/library/asyncio.html) - Programmation asynchrone

### Database

- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) - ORM asynchrone
- [SQLModel] (https://sqlmodel.tiangolo.com/) - Documentation complète

### DevOps & Qualité

- [Pre-commit Framework](https://pre-commit.com/) - Git hooks
- [Ruff Documentation](https://docs.astral.sh/ruff/) - Linter Python rapide
- [Prettier Documentation](https://prettier.io/) - Code formatter
- [Docker Documentation](https://docs.docker.com/) - Containerization
- [Docker Compose](https://docs.docker.com/compose/) - Orchestration multi-conteneurs

### Development Tools

- [VS Code Extensions](https://marketplace.visualstudio.com/) - IDE extensions
- [Git Documentation](https://git-scm.com/doc) - Version control
- [npm Documentation](https://docs.npmjs.com/) - Package manager Node.js

---

## 📞 Support & Contribution

Pour toute question concernant les normes de développement:

1. Consulter ce fichier SKILL.md
2. Vérifier les exemples dans le code existant
3. Consulter la documentation officielle des frameworks
4. Demander aide à l'équipe senior

### Contributions aux normes

Pour proposer des modifications aux normes:

1. Créer une branche `docs/standards-update`
2. Mettre à jour le fichier SKILL.md
3. Créer une Pull Request avec justification
4. Attendre l'approbation de l'équipe

---

## 📝 Historique des versions

| Version | Date       | Changements                                  |
| ------- | ---------- | -------------------------------------------- |
| 1.2.0   | 2026-03-13 | Ajout section documentation                  |
| 1.1.0   | 2026-03-07 | Ajout section pre-commit & erreurs courantes |
| 1.0.0   | 2026-03-07 | Version initiale avec Angular 21 & FastAPI   |

---

**Dernière mise à jour:** 7 Mars 2026
**Statut:** Production Ready ✅
**Mainteneurs:** Portalcrane Development Team
