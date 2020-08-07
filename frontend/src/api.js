import subA from './spoofed_data/sub_a.json'
import subB from './spoofed_data/sub_b.json'
import passStructure from './spoofed_data/pass_structure.json'
import passText from './spoofed_data/pass_text.json'
import passExact from './spoofed_data/pass_exact.json'
import graphData from './spoofed_data/graph.json'

class API {
    static getPasses() {
        return [{"name":passStructure.pass, "docs": passStructure.docs},
                {"name":passText.pass, "docs": passText.docs},
                {"name":passExact.pass, "docs": passExact.docs}];
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
            return passExact;
        }
        if (pass.name === "text") {
            return passText;
        }
        if (pass.name === "structure") {
            return passStructure;
        }
    }
}


export default API;
