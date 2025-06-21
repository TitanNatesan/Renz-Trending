import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz
import re

def validate_gst(gst_number):
    gst_pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$'
    return bool(re.match(gst_pattern, gst_number))

def send_email(
    to_email,
    subject,
    username,
    product_name,
    quantity,
    price,
    total,
    address,
    phone,
    landmark,
    order_date,
):
    # Convert order_date to Asia/Kolkata time zone
    ist = pytz.timezone("Asia/Kolkata")
    order_date_ist = order_date.astimezone(ist)
    order_date_str = order_date_ist.strftime("%Y-%m-%d %H:%M:%S %Z%z")

    # Define the HTML template inline
    email_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f2f2f2;
                line-height: 1.6;
                color: #333333;
            }}
            .email-container {{
                width: 100%;
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                box-sizing: border-box;
            }}
            .header {{
                background-color: #0056b3;
                padding: 20px;
                border-radius: 10px 10px 0 0;
                color: #ffffff;
                text-align: center;
                font-size: 22px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            .content {{
                padding: 20px;
            }}
            .content p {{
                margin: 0 0 10px;
                font-size: 14px;
                line-height: 1.5;
            }}
            .details {{
                background-color: #f7f7f7;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                border: 1px solid #e2e2e2;
            }}
            .details p {{
                margin: 8px 0;
                font-size: 14px;
                color: #555555;
            }}
            .details p strong {{
                color: #333333;
            }}
            .footer {{
                text-align: center;
                color: #aaaaaa;
                font-size: 12px;
                margin-top: 20px;
                padding: 15px;
                border-top: 1px solid #e2e2e2;
            }}
            .footer p {{
                margin: 5px 0;
            }}
            @media (max-width: 600px) {{
                .header {{
                    padding: 15px;
                    font-size: 20px;
                }}
                .content {{
                    padding: 15px;
                }}
                .content p {{
                    font-size: 13px;
                }}
                .details {{
                    padding: 10px;
                }}
                .details p {{
                    font-size: 13px;
                }}
                .footer {{
                    padding: 10px;
                    font-size: 11px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Order Confirmation</h1>
            </div>
            <div class="content">
                <p>Dear {username},</p>
                <p>Thank you for your order. Here are the details:</p>
                <div class="details">
                    <p><strong>Product:</strong> {product_name}</p>
                    <p><strong>Quantity:</strong> {quantity}</p>
                    <p><strong>Price:</strong> ₹{price}</p>
                    <p><strong>Total:</strong> ₹{total}</p>
                    <p><strong>Address:</strong> {address}</p>
                    <p><strong>Phone:</strong> {phone}</p>
                    <p><strong>Landmark:</strong> {landmark}</p>
                    <p><strong>Time:</strong> {order_date_str}</p>
                </div>
                <p>We hope to see you again soon.</p>
            </div>
            <div class="footer">
                <p>&copy; 2024 Your Company. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    sender_email = "natesantitan3@gmail.com"
    sender_password = "wpez xrpu ozrj rgwa"

    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Attach the HTML content to the email
    msg.attach(MIMEText(email_content, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()  # Use TLS for security
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
