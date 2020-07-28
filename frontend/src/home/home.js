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
          <Graph graph='{"data": {"../check50-ja/check50": {"is_archive": false}, "../check50/check50": {"is_archive": false}}, "links": [{"index": 0, "source": "../check50/check50", "target": "../check50-ja/check50", "value": 10.0}], "nodes": [{"id": "../check50-ja/check50"}, {"id": "../check50/check50"}]}' />
        </div>
      </div>
    );
}

export default HomeView;
