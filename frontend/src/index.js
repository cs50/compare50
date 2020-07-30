import React from 'react';
import ReactDOM from 'react-dom';
// import './index.css';
// import './bootstrap.min.css';
//import MatchView from './match/matchview';
import HomeView from './home/home';
import * as serviceWorker from './serviceWorker';

ReactDOM.render(
  <React.StrictMode>
    <HomeView />
  </React.StrictMode>,
  document.getElementById('root')
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
