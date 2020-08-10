// TODO conditionally import mock data
import GRAPH_DATA from './spoofed_data/graph.json'
import SUB_A from './spoofed_data/sub_a.json'
import SUB_B from './spoofed_data/sub_b.json'
import passStructure from './spoofed_data/pass_structure.json'
import passText from './spoofed_data/pass_text.json'
import passExact from './spoofed_data/pass_exact.json'

window.GRAPH_DATA = GRAPH_DATA;

// TODO this should be a build config
const USE_MOCK_DATA = true;

if (USE_MOCK_DATA) {
    window.SUB_A = SUB_A;
    window.SUB_B = SUB_B;
    window.PASSES = [passStructure, passText, passExact]
}

class API {
    static getPasses() {
        return window.PASSES
    }

    static getMatch() {
        return new Match();
    }

    static getGraph(match) {
        return window.GRAPH_DATA;
    }
}


class Match {
    filesA() {
        return window.SUB_A.files;
    }

    filesB() {
        return window.SUB_B.files;
    }

    getPass(pass) {
        return window.PASSES.find(p => p.name === pass.name);
    }
}


export default API;
