export default function Footer(){
    return (
        <footer className="footer container">
            <div className="footer__container grid">
                <div className="footer__content">
                    <Link href="/" className="footer__logo">
                        <Image src="/logo.svg" alt="" className="footer__logo-img" />
                    </Link>
                    <h4 className="footer__subtitle">Contact</h4>
                    <p className="footer__description">
                        <span>Address:</span> 13 Tlemcen Road, Street 32, Beb-Wahren
                    </p>
                    <p className="footer__description">
                        <span>Phone:</span> +01 2222 365 /(+91) 01 2345 6789
                    </p>
                    <p className="footer__description">
                        <span>Hours:</span> 10:00 - 18:00, Mon - Sat
                    </p>
                    <div className="footer__social">
                        <h4 className="footer__subtitle">Follow Me</h4>
                        <div className="footer__links flex">
                            <Link href="#">
                                <Image
                                    src="/icon-facebook.svg"
                                    alt=""
                                    className="footer__social-icon"
                                />
                            </Link>
                            <Link href="#">
                                <Image
                                    src="/icon-twitter.svg"
                                    alt=""
                                    className="footer__social-icon"
                                />
                            </Link>
                            <Link href="#">
                                <Image
                                    src="/icon-instagram.svg"
                                    alt=""
                                    className="footer__social-icon"
                                />
                            </Link>
                            <Link href="#">
                                <Image
                                    src="/icon-pinterest.svg"
                                    alt=""
                                    className="footer__social-icon"
                                />
                            </Link>
                            <Link href="#">
                                <Image
                                    src="/icon-youtube.svg"
                                    alt=""
                                    className="footer__social-icon"
                                />
                            </Link>
                        </div>
                    </div>
                </div>
                <div className="footer__content">
                    <h3 className="footer__title">Address</h3>
                    <ul className="footer__links">
                        <li><Link href="#" className="footer__link">About Us</Link></li>
                        <li><Link href="#" className="footer__link">Delivery Information</Link></li>
                        <li><Link href="#" className="footer__link">Privacy Policy</Link></li>
                        <li><Link href="#" className="footer__link">Terms & Conditions</Link></li>
                        <li><Link href="#" className="footer__link">Contact Us</Link></li>
                        <li><Link href="#" className="footer__link">Support Center</Link></li>
                    </ul>
                </div>
                <div className="footer__content">
                    <h3 className="footer__title">My Account</h3>
                    <ul className="footer__links">
                        <li><Link href="#" className="footer__link">Sign In</Link></li>
                        <li><Link href="#" className="footer__link">View Cart</Link></li>
                        <li><Link href="#" className="footer__link">My Wishlist</Link></li>
                        <li><Link href="#" className="footer__link">Track My Order</Link></li>
                        <li><Link href="#" className="footer__link">Help</Link></li>
                        <li><Link href="#" className="footer__link">Order</Link></li>
                    </ul>
                </div>
                <div className="footer__content">
                    <h3 className="footer__title">Secured Payed Gateways</h3>
                    <Image
                        src="/payment-method.png"
                        alt=""
                        className="payment__img"
                    />
                </div>
            </div>
            <div className="footer__bottom">
                <p className="copyright">&copy; 2024 Evara. All right reserved</p>
                <span className="designer">Designer by Crypticalcoder</span>
            </div>
        </footer>
    )
}