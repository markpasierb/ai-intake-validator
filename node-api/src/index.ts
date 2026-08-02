import express from "express";
import cors from "cors";

const app = express();
const port = 3000;

const PYTHON_API = "http://127.0.0.1:8000";

app.use(
  cors({
    origin: "http://localhost:5173",
  }),
);

app.use(express.json());

app.get("/health", (_req, res) => {
    res.json({
        status: "ok",
        service: "node-api",
    });
});

app.post("/intake", async (req, res) => {
    try {
        const response = await fetch(`${PYTHON_API}/intake`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(req.body),
        });

        if (!response.ok) {
            return res.status(response.status).json({
                error: "Python service returned an error",
            });
        }

        const data = await response.json();

        res.json(data);
    }
    catch (err) {
        console.error(err);

        res.status(500).json({
            error: "Unable to contact AI service",
        });
    }
});

app.listen(port, () => {
    console.log(`Node API listening on port ${port}`);
});