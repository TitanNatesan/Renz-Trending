
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, EffectCoverflow } from 'swiper/modules';
import Image from "next/image";
import "@/app/globals.css"
import { baseurl } from "@/app/utils/Url";
import { ArrowLeft, ArrowRight } from "lucide-react";


export default function Categories({ categories }) {
  return (
    <section className="categories container section">
      <h3 className="section__title" data-aos="fade-right"><span>Popular</span> Categories</h3>
      <Swiper
        className="categories__container swiper"
        spaceBetween={20}
        loop={true}
        grabCursor={true}
        modules={[Navigation, EffectCoverflow]}
        coverflowEffect={{
          rotate: 10,
          stretch: 1,
          depth: 100,
          modifier: 1,
          slideShadows: true,
          scale: .95,
        }}
        navigation={{
          nextEl: ".swiper-button-next",
          prevEl: ".swiper-button-prev",
        }}
        breakpoints={{
          350: { slidesPerView: 2, spaceBetween: 24 },
          768: { slidesPerView: 3, spaceBetween: 24 },
          992: { slidesPerView: 4, spaceBetween: 24 },
          1200: { slidesPerView: 5, spaceBetween: 24 },
          1400: { slidesPerView: 6, spaceBetween: 24 },
        }}
        effect="coverflow"
        autoHeight={false}
      >

        <div className="swiper-wrapper">
          {categories.map((category, index) => (
            <SwiperSlide key={index} virtualIndex={index} className="h-full rounded-lg category__item-wrapper" data-aos="fade-up" data-aos-delay={index * 100}>
              <a href="/shop" className="category__item w-full" data-aos="fade-up" data-aos-anchor-placement="top-bottom" data-aos-delay={index * 150}>
                <Image
                  src={baseurl + "/" + category.image}
                  width={150}
                  height={200}
                  alt={category.name}
                  className="category__img"
                />
                <h3 className="category__title">{category.name}</h3>
              </a>
            </SwiperSlide>
          ))}
        </div>

      </Swiper>
      <div className="swiper-button-prev mr-3" data-aos="fade-left">
        <ArrowLeft size={16} fontWeight={700} />
      </div>
      <div className="swiper-button-next mr-3" data-aos="fade-right">
        <ArrowRight size={16} fontWeight={700} />
      </div>
    </section>
  )
}