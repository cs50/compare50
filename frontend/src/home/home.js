import React from 'react';
import ReactDOM from 'react-dom';
import '../index.css';
import * as serviceWorker from '../serviceWorker';
import Logo from '../match/logo';
import Graph from './graph'

import API from '../api';


function HomeView() {
    return (
      <div>
        <div>
          <Logo />
        </div>
        <div>
          <Graph />
        </div>
      </div>
    );
}

export default HomeView;
