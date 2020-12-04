import React from 'react';


function Logo(props) {
    return (
        <div 
            onClick={() => window.location.href = "home.html"}
            style={{
                "fontWeight": "bold",
                "width": "100%",
                "height": props.height,
                "lineHeight": props.height,
                "textAlign": "center",
                "cursor": "pointer"
            }}
        >
            compare50
        </div>
    )
}

export default Logo;
