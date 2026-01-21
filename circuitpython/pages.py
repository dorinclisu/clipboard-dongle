HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clipboard Dongle</title>
    <link rel="icon" type="image/png" href="/clipboard.png">
    <link rel="apple-touch-icon" href="/clipboard.png">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        textarea {
            width: 100%;
            min-height: 200px;
            padding: 10px;
            font-family: monospace;
            font-size: 14px;
            border: 2px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
            resize: vertical;
            overflow-y: scroll;
        }
        textarea:focus {
            outline: none;
            border-color: #4CAF50;
        }
        .button-group {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        button {
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .submit-btn {
            background-color: #4CAF50;
            color: white;
            flex: 1;
        }
        .submit-btn:hover {
            background-color: #45a049;
        }
        .clear-btn {
            background-color: #f44336;
            color: white;
        }
        .clear-btn:hover {
            background-color: #da190b;
        }
        .message {
            margin-top: 15px;
            padding: 10px;
            border-radius: 5px;
            display: none;
        }
        .message.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 14px;
        }
        .footer a {
            color: #4CAF50;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{NAME}</h1>
        <form id="textForm">
            <textarea id="textInput" placeholder="Enter your text here..."></textarea>
            <div class="button-group">
                <button type="submit" class="submit-btn">Send</button>
                <button type="button" class="clear-btn" onclick="clearText()">Clear</button>
            </div>
        </form>
        <div id="message" class="message"></div>
        <div class="footer">
            Made by <a href="https://github.com/dorinclisu" target="_blank">Dorin Clisu</a>
        </div>
    </div>
    <script>
        function clearText() {
            document.getElementById('textInput').value = '';
            document.getElementById('textInput').focus();
        }

        document.getElementById('textForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const text = document.getElementById('textInput').value;
            const messageDiv = document.getElementById('message');

            fetch('/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'text/plain'
                },
                body: text
            })
            .then(response => {
                if (response.ok) {
                    messageDiv.textContent = 'Text sent successfully!';
                    messageDiv.className = 'message success';
                    messageDiv.style.display = 'block';
                    setTimeout(() => {
                        messageDiv.style.display = 'none';
                    }, 3000);
                } else {
                    return response.text().then(errorText => {
                        throw new Error(errorText || 'Failed to send');
                    });
                }
            })
            .catch(error => {
                messageDiv.textContent = error.message;
                messageDiv.className = 'message error';
                messageDiv.style.display = 'block';
            });
        });
    </script>
</body>
</html>
"""
