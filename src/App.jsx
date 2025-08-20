import { useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";
import "./App.css";
import ChatBot from "./components/ChatBot";
import doctorImg from "./assets/doctor.png";
import classes from "./app.module.scss";

function App() {
    return (
        <>
            <img
                className={classes.logoImg}
                src={doctorImg}
                alt="doctor logo"
            />
            <ChatBot />
        </>
    );
}

export default App;
