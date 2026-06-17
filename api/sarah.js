// api/sarah.js — Vercel serverless function
// Keeps your Anthropic API key server-side. The page never sees it.
// Set ANTHROPIC_API_KEY in Vercel project environment variables.

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const { messages, system } = req.body;

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: "messages array required" });
    }

    // Cap history length to control cost / abuse
    const trimmed = messages.slice(-12);

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": process.env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-haiku-4-5-20251001",
        max_tokens: 300,
        system: system || "You are Sarah, a warm empathetic guide helping people find therapy through BetterHelp. Keep replies to 2-3 sentences. Never diagnose. If crisis or self-harm is mentioned, tell them to call or text 988 immediately.",
        messages: trimmed,
      }),
    });

    const data = await response.json();
    const reply =
      data?.content?.[0]?.text || "I'm here. Tell me a little more.";

    return res.status(200).json({ reply });
  } catch (err) {
    console.error("Sarah error:", err);
    return res
      .status(200)
      .json({ reply: "I'm here — give me a moment and try again." });
  }
}
