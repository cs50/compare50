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
          <Graph graph='{"data": {"../compare50-cs50/compare50/_renderer/static": {"is_archive": false}, "compare50/_renderer/static": {"is_archive": false}, "frontend/src/home": {"is_archive": false}}, "links": [{"index": 0, "source": "compare50/_renderer/static", "target": "../compare50-cs50/compare50/_renderer/static", "value": 10.0}, {"index": 1, "source": "frontend/src/home", "target": "compare50/_renderer/static", "value": 2.1115042573076015}, {"index": 2, "source": "frontend/src/home", "target": "../compare50-cs50/compare50/_renderer/static", "value": 2.1115042573076015}, {"index": 3, "source": "frontend/src/home", "target": "compare50/_renderer/static", "value": 1.1703741938222783}, {"index": 4, "source": "frontend/src/home", "target": "../compare50-cs50/compare50/_renderer/static", "value": 1.1703741938222783}, {"index": 5, "source": "frontend/src/home", "target": "frontend/src/home", "value": 0.25548248403004065}], "nodes": [{"id": "compare50/_renderer/static"}, {"id": "frontend/src/home"}, {"id": "../compare50-cs50/compare50/_renderer/static"}, {"id": "frontend/src/home"}]}' />
        </div>
      </div>
    );
}

export default HomeView;
