# HTS Oracle Frontend

[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=white)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.9+-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5+-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)

> Modern, accessible React frontend for the HTS Oracle classification system with enterprise-grade UX and professional design.

## 🎯 **Overview**

The HTS Oracle frontend is a sophisticated React application built with enterprise accessibility standards, modern design principles, and professional user experience patterns. It provides an intuitive interface for HTS product classification with contextual help, progressive disclosure, and comprehensive export capabilities.

## ✨ **Key Features**

- **🎨 Modern Design System**: Professional typography, spacing, and color palette
- **♿ Enterprise Accessibility**: WCAG 2.1 AA compliant with screen reader support
- **📱 Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **🔄 Progressive Disclosure**: Smart information hierarchy with expandable details
- **📚 Contextual Help**: 4-tab help system with guidance and examples
- **📊 Professional Export**: HTML reports for customs documentation
- **⚡ Real-time Search**: Instant feedback with skeleton loading states
- **🎯 Focus Management**: Professional keyboard navigation and accessibility

## 🏗️ **Architecture**

### Component Structure

```
src/
├── components/
│   ├── layout/
│   │   ├── Header.jsx          # Main navigation and branding
│   │   └── Layout.jsx          # App layout wrapper
│   │
│   ├── search/
│   │   ├── SearchForm.jsx      # Search input with hints
│   │   ├── SearchActions.jsx   # Search controls
│   │   └── SearchHints.jsx     # Interactive examples
│   │
│   ├── results/
│   │   ├── ResultsContainer.jsx # Results layout wrapper
│   │   ├── ResultCard.jsx      # Individual HTS result
│   │   ├── HTSDetails.jsx      # Detailed classification info
│   │   └── ExportButton.jsx    # PDF/HTML export
│   │
│   └── shared/
│       ├── LoadingStates.jsx   # Skeleton loaders
│       ├── AccessibilityProvider.jsx # A11y context
│       └── HelpSystem.jsx      # Contextual guidance
│
├── utils/
│   ├── pdfExport.js           # HTML report generation
│   ├── formatters.js          # Data formatting utilities
│   └── accessibility.js       # A11y helper functions
│
└── styles/
    └── App.css               # Design system styles
```

### Design System

#### Typography Scale
- **H1**: 36px/44px (Main titles)
- **H2**: 30px/36px (Section headers)  
- **H3**: 24px/28px (Card titles)
- **Body**: 16px/24px (Content text)
- **Small**: 14px/20px (Metadata)

#### Color Palette
- **Primary**: Blue 600 (#2563eb)
- **Success**: Green 600 (#16a34a)
- **Warning**: Amber 500 (#f59e0b)
- **Error**: Red 600 (#dc2626)
- **Neutral**: Gray 50-900 scale

#### Spacing System
- **XS**: 8px, **SM**: 12px, **MD**: 16px
- **LG**: 24px, **XL**: 32px, **2XL**: 48px

## 🚀 **Quick Start**

### Prerequisites

- **Node.js 18+** with npm
- **Backend API** running on port 8000

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/hts-oracle.git
cd hts-oracle/frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.development
# Edit .env.development with your backend URL

# Start development server
npm run dev
```

The application will start on `http://localhost:5173`

### Environment Configuration

Create `.env.development`:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Optional: Enable debug mode
VITE_DEBUG=true
```

For production, create `.env.production`:

```bash
# Production API URL
VITE_API_URL=https://your-api-domain.com

# Disable debug
VITE_DEBUG=false
```

## 📖 **Usage**

### Basic Workflow

1. **Enter Product Description**: Use the search form with guided examples
2. **Review Classifications**: Progressive disclosure shows relevant details
3. **Explore Details**: Expand cards for duty rates and regulatory info
4. **Export Results**: Generate professional HTML reports
5. **Access Help**: Use contextual help for classification guidance

### Search Best Practices

```
✅ Good Examples:
- "100% cotton knitted t-shirts for men"
- "Stainless steel pipes for construction, 2-inch diameter"
- "LED light bulbs, 60-watt equivalent, household use"

❌ Avoid:
- "Nike shirts" (brand names)
- "Machine parts" (too vague)
- "Stuff from China" (not descriptive)
```

### Accessibility Features

- **Keyboard Navigation**: Tab through all interactive elements
- **Screen Readers**: Comprehensive ARIA labels and descriptions
- **Focus Management**: Clear visual indicators and logical flow
- **High Contrast**: Compatible with system preferences
- **Reduced Motion**: Respects user accessibility settings

## 🛠️ **Development**

### Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# E2E tests
npm run test:e2e

# Accessibility tests
npm run test:accessibility

# Lint code
npm run lint

# Type checking
npm run type-check
```

### Development Guidelines

#### Code Style

- Use **TypeScript** for type safety
- Follow **React functional components** pattern
- Implement **custom hooks** for logic separation
- Use **CSS modules** or **styled-components** for styling
- Follow **accessibility-first** development

#### Component Guidelines

```jsx
// Good: Accessible component structure
const SearchForm = ({ onSubmit, loading }) => {
  return (
    <form onSubmit={onSubmit} role="search">
      <label htmlFor="search-input" className="sr-only">
        Product description
      </label>
      <input
        id="search-input"
        type="text"
        placeholder="Describe your product..."
        aria-describedby="search-hint"
        disabled={loading}
      />
      <div id="search-hint" className="text-sm text-gray-600">
        Be specific about materials, use, and dimensions
      </div>
    </form>
  );
};
```

#### State Management

```jsx
// Use React hooks for local state
const [searchQuery, setSearchQuery] = useState('');
const [results, setResults] = useState([]);
const [loading, setLoading] = useState(false);

// Custom hooks for complex logic
const useHTSClassification = () => {
  // Classification logic here
  return { classify, loading, error };
};
```

### Testing

#### Unit Tests

```bash
# Test individual components
npm run test SearchForm.test.jsx

# Test with coverage
npm run test:coverage
```

#### E2E Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run specific test suite
npm run test:e2e -- --grep "classification"

# Debug mode
npm run test:e2e:debug
```

#### Accessibility Tests

```bash
# Automated accessibility testing
npm run test:accessibility

# Manual testing checklist
npm run test:a11y:manual
```

## 🎨 **Design System Implementation**

### CSS Architecture

```css
/* Base styles with CSS custom properties */
:root {
  /* Typography */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  
  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  
  /* Colors */
  --color-primary: #2563eb;
  --color-success: #16a34a;
  --color-warning: #f59e0b;
  --color-error: #dc2626;
}
```

### Component Styling

```jsx
// Use CSS modules or styled-components
import styles from './SearchForm.module.css';

const SearchForm = () => (
  <div className={styles.container}>
    <input className={styles.input} />
    <button className={styles.button}>Search</button>
  </div>
);
```

### Responsive Design

```css
/* Mobile-first responsive design */
.container {
  padding: var(--space-4);
}

@media (min-width: 768px) {
  .container {
    padding: var(--space-6);
  }
}

@media (min-width: 1024px) {
  .container {
    padding: var(--space-8);
  }
}
```

## 📊 **API Integration**

### Classification Service

```javascript
// utils/api.js
const classifyProduct = async (query) => {
  const response = await fetch(`${API_URL}/api/classify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  
  if (!response.ok) {
    throw new Error('Classification failed');
  }
  
  return response.json();
};
```

### Error Handling

```javascript
const useHTSClassification = () => {
  const [state, setState] = useState({
    data: null,
    loading: false,
    error: null,
  });
  
  const classify = async (query) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const result = await classifyProduct(query);
      setState({ data: result, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error.message });
    }
  };
  
  return { ...state, classify };
};
```

## 📱 **Browser Support**

- **Chrome** 90+
- **Firefox** 88+
- **Safari** 14+
- **Edge** 90+

## 🔧 **Build Configuration**

### Vite Configuration

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          utils: ['./src/utils'],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
```

### TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

## 🚀 **Deployment**

### Production Build

```bash
# Create production build
npm run build

# Preview production build locally
npm run preview

# Deploy to static hosting
npm run deploy
```

### Netlify Configuration

```toml
# netlify.toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[build.environment]
  VITE_API_URL = "https://your-api-domain.com"
```

### Performance Optimization

- **Code Splitting**: Automatic chunking for optimal loading
- **Tree Shaking**: Remove unused code
- **Asset Optimization**: Compressed images and minified CSS/JS
- **Caching**: Efficient browser caching strategy

## 🔒 **Security**

### Environment Variables

- Store sensitive config in environment variables
- Never commit `.env` files to version control
- Use different configs for development/production
- Validate environment variables at startup

### Content Security Policy

```html
<!-- Recommended CSP headers -->
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline'; 
               connect-src 'self' https://api.your-domain.com;">
```

## 📈 **Performance Monitoring**

### Core Web Vitals

- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

### Optimization Techniques

- Lazy loading of components
- Image optimization and responsive images
- Efficient state management
- Memoization of expensive calculations
- Debounced search inputs

## 🤝 **Contributing**

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install dependencies: `npm install`
4. Start development server: `npm run dev`
5. Make your changes with tests
6. Run tests: `npm run test`
7. Check accessibility: `npm run test:accessibility`
8. Submit a pull request

### Code Review Checklist

- [ ] TypeScript types are correctly defined
- [ ] Components are accessible (ARIA labels, keyboard nav)
- [ ] Tests cover new functionality
- [ ] Documentation is updated
- [ ] Performance impact is considered
- [ ] Error handling is implemented
- [ ] Mobile responsiveness is tested

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

For backend API documentation, see [Backend README](../backend/README.md)
For project overview, see [Main README](../README.md)