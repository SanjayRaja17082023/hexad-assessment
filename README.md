# Hexad Assessment: Book Borrowing System (Frontend)

This project is a React + TypeScript frontend for a book borrowing and returning system, designed for the Hexad Full Stack Developer assessment. It features role-based authentication (User/Admin), book inventory management, admin controls, and a mocked backend using MSW.

## Features
- User and Admin roles with authentication (mocked Google/GitHub login)
- Borrow up to 2 books, return books, and view stock status
- Admin can add/update books, view inventory, and track borrowed/returned books
- Intuitive, user-friendly UI with clear stock indicators
- Error handling for 400, 401, 403 responses
- MSW for backend API mocking
- ESLint and Prettier for code quality
- Unit and integration tests with Jest and React Testing Library

## Folder Structure
- `src/components`: Reusable UI components
- `src/pages`: Application pages (Home, Login, Admin, etc.)
- `src/services`: API and business logic
- `src/types`: TypeScript types and interfaces
- `src/context`: React context for global state
- `src/tests`: Test files

## Setup
1. Install dependencies: `npm install`
2. Start development server: `npm start`
3. Run tests: `npm test`

## Coding Standards
- Follows SOLID principles and best practices
- Clean commit history for every change
- Private repository for assessment

---
# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `npm run eject`

**Note: this is a one-way operation. Once you `eject`, you can’t go back!**

If you aren’t satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you’re on your own.

You don’t have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn’t feel obligated to use this feature. However we understand that this tool wouldn’t be useful if you couldn’t customize it when you are ready for it.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).
