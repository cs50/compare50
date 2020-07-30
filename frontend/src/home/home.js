import React from 'react';
import '../index.css';
import Logo from '../match/logo';
import Graph from './graph'

function HomeView() {
    return (
        <div>
            <div>
                <Logo />
            </div>
            <div>
                <Graph
                  graph='{"data": {"../check50-ja/check50": {"is_archive": false}, "../check50/check50": {"is_archive": false}, "../compare50-cs50/compare50/_renderer/static": {"is_archive": false}, "compare50/_renderer/static": {"is_archive": false}, "frontend/src/home": {"is_archive": false}}, "links": [{"index": 0, "source": "compare50/_renderer/static", "target": "../compare50-cs50/compare50/_renderer/static", "value": 10.0}, {"index": 1, "source": "frontend/src/home", "target": "compare50/_renderer/static", "value": 2.069944789491055}, {"index": 2, "source": "frontend/src/home", "target": "../compare50-cs50/compare50/_renderer/static", "value": 2.069944789491055}, {"index": 3, "source": "../check50/check50", "target": "../check50-ja/check50", "value": 1.6379459124980762}], "nodes": [{"id": "../check50-ja/check50"}, {"id": "../check50/check50"}, {"id": "../compare50-cs50/compare50/_renderer/static"}, {"id": "compare50/_renderer/static"}, {"id": "frontend/src/home"}]}'
                  height="300" />
            </div>
      </div>
    );
}

export default HomeView;
