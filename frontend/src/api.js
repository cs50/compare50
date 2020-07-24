import sub_a from './spoofed_data/sub_a.json'
import sub_b from './spoofed_data/sub_a.json'
import match_structure from './spoofed_data/match_structure.json'


class API {
    static passes = ["structure", "text", "exact"];

    static get_match() {
        return new Match();
    }
}


class Match {
    files_a() {
        return sub_a.files;
    }

    files_b() {
        return sub_b.files;
    }

    get_pass(pass) {
        return match_structure;
    }
}


export default API;
