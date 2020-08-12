import React from 'react';
import ReactDOM from 'react-dom';
import {Helmet} from "react-helmet";
import * as serviceWorker from './serviceWorker';

// https://blog.logrocket.com/multiple-entry-points-in-create-react-app-without-ejecting/
let BuildTarget = null;
if (process.env.REACT_APP_BUILD_TARGET === "home") {
    BuildTarget = require("./home/home").default;
}
else if (process.env.REACT_APP_BUILD_TARGET === "match") {
    BuildTarget = require("./match/matchview").default;
}
else {
    throw new Error(`Env var REACT_APP_BUILD_TARGET is not set to either 'home' or 'match'`);
}

// Source SVGs (and emoji's) as favicon: https://stackoverflow.com/a/62438464
ReactDOM.render(
    <React.StrictMode>
        <Helmet>
            <title>compare50</title>
            <link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2016%2016'%3E%3Ctext%20x='0'%20y='14'%3E📝%3C/text%3E%3C/svg%3E" type="image/svg+xml" />
        </Helmet>
        <BuildTarget />
    </React.StrictMode>,
    document.getElementById("root")
)

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
