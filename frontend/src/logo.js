import React from 'react';


function Logo(props) {
    return (
        <div style={{
            "fontWeight":"bold",
            "width":"100%",
            "height":props.height,
            "lineHeight":props.height,
            "textAlign":"center"
        }}>
            compare50
        </div>
    )
}

export default Logo;
