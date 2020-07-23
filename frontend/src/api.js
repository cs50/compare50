import sub_a from './spoofed_data/sub_a.json'
import sub_b from './spoofed_data/sub_a.json'


class API {
    static passes = ["structure", "text", "exact"];

    static get_match() {
        return new Match();
    }
}


class Match {
    code_a() {
        return sub_a.code;
    }

    code_b() {
        return sub_b.code;
    }
}


export default API;
