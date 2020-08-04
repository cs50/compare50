import subA from './spoofed_data/sub_a.json'
import subB from './spoofed_data/sub_b.json'
import matchStructure from './spoofed_data/match_structure.json'
import matchText from './spoofed_data/match_text.json'
import matchExact from './spoofed_data/match_exact.json'
import graphData from './spoofed_data/graph.json'
import passes from './spoofed_data/passes.json'


class API {
    static getPasses() {
        return passes;
    }

    static getMatch() {
        return new Match();
    }

    static getGraph(match) {
        return graphData;
    }
}


class Match {
    filesA() {
        return subA.files;
    }

    filesB() {
        return subB.files;
    }

    getPass(pass) {
        if (pass.name === "exact") {
            return matchExact;
        }
        if (pass.name === "text") {
            return matchText;
        }
        if (pass.name === "structure") {
            return matchStructure;
        }
    }
}


export default API;
