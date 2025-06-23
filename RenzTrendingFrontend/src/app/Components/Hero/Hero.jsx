import Image from "next/image";

export default function Hero() {
    return (
        <section className="home section--lg">
            <div className="home__container container grid">
                <div className="home__content">
                    <span className="home__subtitle" data-aos="fade-right" data-aos-delay="50">Renz Trending</span>
                    <h1 className="home__title" data-aos="fade-right" data-aos-delay="150">
                        Fashion Products <span>Great Collection</span>
                    </h1>
                    <p className="home__description" data-aos="fade-right" data-aos-delay="250">
                        Save more from buying products directly from the manufacturers
                    </p>
                    <a href="/shop" className="btn" data-aos="zoom-in" data-aos-delay="100" data-aos-duration="600">Shop Now</a>
                </div>
                <Image data-aos="zoom-in" src={"/logo.png"} width={1500} height={1000} className="home__img" alt="hats" priority={true} />
            </div>
        </section>
    )
}