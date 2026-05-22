# Import Error Analysis & Fix

## Problem
Server fails to start with "ImportError: attempted relative import with no known parent package"

## Root Cause Analysis

### Code Structure
```
/app/
  ├── backend/
  │   ├── server.py (main file, does: from revenue_operations_integration import...)
  │   ├── seed.py
  │   ├── recovery.py
  │   ├── revenue_operations_integration.py (does: from .billing.stripe_service import...)
  │   ├── billing/
  │   │   ├── stripe_service.py (does: from .models import...)
  │   │   └── models.py
  │   └── __init__.py
  │
  └── src/
      └── agents/
          └── pipeline_manager.py
```

### Import Patterns Used

1. **Backend local imports** (from `/app/backend/server.py`):
   - `from seed import MODULES`
   - `from revenue_operations_integration import init_revenue_operations`
   - These expect to find modules in `/app/backend/`

2. **Relative imports** (from `/app/backend/revenue_operations_integration.py`):
   - `from .billing.stripe_service import StripeService`
   - These are relative imports within the backend package

3. **Src imports** (from `/app/backend/server.py`):
   - `from src.agents.pipeline_manager import PipelineManager`
   - These expect to find modules starting from `/app`

### Why It Fails

When Docker runs:
- `WORKDIR /app/backend`
- `PYTHONPATH=/app`
- `CMD uvicorn server:app`

Python looks for:
1. `from seed import` → looks in PYTHONPATH `/app`, doesn't find `/app/backend/seed.py` ❌
2. `from src.agents import` → looks in PYTHONPATH `/app`, finds `/app/src/` ✓

### The Fix

Set `PYTHONPATH` to include BOTH locations:
```dockerfile
ENV PYTHONPATH=/app/backend:/app
```

This way:
- `from seed import` finds `/app/backend/seed.py` (checked first in path)
- `from .billing.stripe_service import` works (relative import from same package)
- `from src.agents import` finds `/app/src/agents/` (checked second in path)

## Verification

The fix should:
1. Allow server.py to import from backend modules ✓
2. Allow relative imports in billing/stripe_service.py to work ✓
3. Allow imports from src/ modules to work ✓

## Implementation

Change Dockerfile line 8 from:
```dockerfile
ENV PYTHONPATH=/app
```

To:
```dockerfile
ENV PYTHONPATH=/app/backend:/app
```

This is the **long-term correct architecture** that properly maps Python's import search path to our directory structure.
