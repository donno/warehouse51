toys
====
Various little scripts and toys, that aim to be more proof-of-concept and
demonstrate a particular idea. Not quite developed enough to be standing on its
own or deserving of its own folder / part of a bigger project.

notepad-llama.py
----------------
Watch for an untitled Notepad window for a line starting with !prompt
followed by the prompt to send to LLaMA (language model) and ending with "!!".
The LLaMA model is expected to be hosted by llama-cpp's simple server program
(on localhost:8080) and the result replaces the prompt line=.