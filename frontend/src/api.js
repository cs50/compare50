const IN_DEVELOPMENT = process.env.NODE_ENV === "development";


class API {
    static placeHolderMatch() {
        return new Match(
            {
                "name": "...",
                "files": [],
                "id": -1,
                "isArchive": false
            },
            {
                "name": "...",
                "files": [],
                "id": -2,
                "isArchive": false
            },
            []
        )
    }

    static async getMatch() {
        // In development use mock data
        if (IN_DEVELOPMENT) {
            return await Promise.all([
                import('./mock_data/sub_a.json'),
                import('./mock_data/sub_b.json'),
                import('./mock_data/pass_structure.json'),
                import('./mock_data/pass_text.json'),
                import('./mock_data/pass_exact.json'),
                import('./mock_data/match_metadata.json')
            ])
            .then(([subA, subB, passStructure, passText, passExact, metadata]) => {
                return new Match(subA, subB, [passStructure, passText, passExact], metadata);
            });
        }

        // In production use static data attached to the window by compare50
        return new Match(window.COMPARE50.SUB_A, window.COMPARE50.SUB_B, window.COMPARE50.PASSES, window.COMPARE50.METADATA);
    }

    static async getGraph() {
        // In development use mock data
        if (IN_DEVELOPMENT) {
            return await Promise.all([
                import('./mock_data/home_links.json'),
                import('./mock_data/home_submissions.json')
            ])
            .then(([links, submissions]) => {
                return new Graph(links.default, submissions.default).inD3Format();
            });
        }

        // In production use static data attached to the window by compare50
        return new Graph(window.COMPARE50.LINKS, window.COMPARE50.SUBMISSIONS).inD3Format();
    }
}


class Match {
    constructor(subA, subB, passes, metadata) {
        this.subA = subA;
        this.subB = subB;
        this.passes = passes;
        this.metadata = metadata;
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

    index() {
        return this.metadata.index;
    }

    numberOfMatches() {
        return this.metadata.numberOfMatches;
    }
}


class Graph {
    constructor(links, submissions) {
        this.links = links;
        this.submissions = submissions;
    }

    inD3Format() {
        const d3Format = {};

        // Create data field
        const data = {};
        for (let id in this.submissions) {
            let sub = this.submissions[id];
            data[sub.path] = {
                "is_archive": sub.isArchive
            }
        }
        d3Format["data"] = data;

        // Create links field
        d3Format["links"] = this.links.map((link, i) => {
            return {
                "index": i,
                "link_index": link.index,
                "source": this.submissions[link.submissionIdA].path,
                "target": this.submissions[link.submissionIdB].path,
                "value": link.normalized_score
            };
        });

        // Create nodes field
        const nodes = [];
        for (let id in this.submissions) {
            let sub = this.submissions[id];
            nodes.push({
                "id": sub.path
            });
        }
        d3Format["nodes"] = nodes;

        return d3Format;
    }
}


export default API;
