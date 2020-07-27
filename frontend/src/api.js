import subA from './spoofed_data/sub_a.json'
import subB from './spoofed_data/sub_b.json'
import matchStructure from './spoofed_data/match_structure.json'


class API {
    static getPasses() {
        return [
            {"name": "structure", "docs":"foo"},
            {"name": "text", "docs": "bar"},
            {"name": "exact", "docs": "baz"}
        ]
    }

    static getMatch() {
        return new Match();
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
        return matchStructure;
    }
}


export default API;
