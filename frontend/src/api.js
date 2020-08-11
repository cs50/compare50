import GRAPH_DATA from './spoofed_data/graph.json'

window.GRAPH_DATA = GRAPH_DATA;

const IN_DEVELOPMENT = process.env.NODE_ENV === "development";

if (IN_DEVELOPMENT) {
    _load_data = Promise.all([
        import('./spoofed_data/sub_a.json'),
        import('./spoofed_data/sub_b.json'),
        import('./spoofed_data/pass_structure.json'),
        import('./spoofed_data/pass_text.json'),
        import('./spoofed_data/pass_exact.json')
    ])
    .then(([subA, subB, passStructure, passText, passExact]) => {
        window.SUB_A = subA;
        window.SUB_B = subB;
        window.PASSES = [
            passStructure,
            passText,
            passExact
        ];
    })
} else {
    var _load_data = (async () => {})();
}


class API {
    static async getMatch() {
        await _load_data;
        return new Match();
    }

    static async getGraph() {
        await _load_data;
        return window.GRAPH_DATA;
    }
}


class Match {
    passes() {
        return window.PASSES
    }

    getPass(pass) {
        return window.PASSES.find(p => p.name === pass.name);
    }

    filesA() {
        return window.SUB_A.files;
    }

    filesB() {
        return window.SUB_B.files;
    }
}


export default API;
