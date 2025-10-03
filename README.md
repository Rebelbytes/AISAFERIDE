# Saferide AI Project

This project consists of a backend API service and a frontend React application for detecting and managing traffic violations using AI.

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Git

## Backend Setup

1. Navigate to the backend directory:

```bash
cd saferide_backend
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install backend dependencies:

```bash
pip install -r requirements.txt
```

4. Apply database migrations:

```bash
python manage.py migrate
```

5. Run the backend development server:

```bash
python manage.py runserver
```

The backend API will be available at `http://127.0.0.1:8000/`.

## Frontend Setup

1. Navigate to the frontend directory:

```bash
cd saferide_frontend
```

2. Install frontend dependencies:

```bash
npm install
# or
yarn install
```

3. Start the frontend development server:

```bash
npm start
# or
yarn start
```

The frontend app will be available at `http://localhost:3000/`.

## Usage

- Upload media files (images/videos) via the frontend.
- The AI detection runs and shows annotated media with detected violations.
- Violations are displayed in categorized sections.
- You can save individual violations for record-keeping.

## Notes

- Ensure the backend server is running before starting the frontend.
- Media files and violation images are served from the backend.
- The project uses Tailwind CSS for styling and Framer Motion for animations.

## Troubleshooting

- If ports 8000 or 3000 are in use, change them accordingly in backend and frontend configs.
- For any issues with dependencies, try deleting `node_modules` and reinstalling.

## License

This project is licensed under the MIT License.
