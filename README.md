# Cricket Machine Learning Project Website

This project is a cricket-focused machine learning website built with React and Vite. It follows the academic project structure requested for an ML assignment and includes all required tabs: Introduction, DataPrep_EDA, Clustering, PCA, NaiveBayes, DecTrees, SVMs, Regression, NN, and Conclusions.

## API and data focus

The project is designed around cricket data and uses a sports API approach for data collection. For local development, create a `.env.local` file in the project root with:

VITE_CRICAPI_KEY=your_key_here

A sample query structure is shown in the DataPrep/EDA tab and can be used with a sports API endpoint such as:

https://api.cricapi.com/v1/currentMatches?apikey=YOUR_API_KEY&offset=0

Do not commit `.env.local` or any real API key to GitHub.

## Getting started

1. Install dependencies:
   npm install
2. Start the development server:
   npm run dev
3. Build for production:
   npm run build

## Project structure

- src/App.jsx: main website content and tab layout
- src/App.css: styling for the academic website
- src/index.css: global site styles

## Notes

The project is ready to be customized further with real exported cricket CSV files, additional model notebooks, and a final polished academic report.
