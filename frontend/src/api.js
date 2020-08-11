import GRAPH_DATA from './mock_data/graph.json'

window.GRAPH_DATA = GRAPH_DATA;

const IN_DEVELOPMENT = process.env.NODE_ENV === "development";


class API {
    static async getMatch() {
        // In development use mock data
        if (IN_DEVELOPMENT) {
            return await Promise.all([
                import('./mock_data/sub_a.json'),
                import('./mock_data/sub_b.json'),
                import('./mock_data/pass_structure.json'),
                import('./mock_data/pass_text.json'),
                import('./mock_data/pass_exact.json')
            ])
            .then(([subA, subB, passStructure, passText, passExact]) => {
                return new Match(subA, subB, [passStructure, passText, passExact]);
            });
        }

        // In production use static data attached to the window by compare50
        return new Match(window.SUB_A, window.SUB_B, window.PASSES);
    }

    static getGraph() {
        return window.GRAPH_DATA;
    }
}


class Match {
    constructor(subA, subB, passes) {
        this.subA = subA;
        this.subB = subB;
        this.passes = passes;
    }

    getPass(pass) {
        return this.passes.find(p => p.name === pass.name);
    }

    filesA() {
        return this.subA.files;
    }

    filesB() {
        return this.subB.files;
    }
}


export default API;
