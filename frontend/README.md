# PDFStract Frontend

React + Vite + ShadCN UI frontend for PDFStract.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

The built files will be in `../static` directory, which FastAPI will serve.

## Development

The Vite dev server runs on port 5173 by default and proxies API requests to the FastAPI backend on port 8000.

## Production

After building, the static files are served directly by FastAPI from the `static` directory.

