
const IMAGE_MAP = {
  'Аквапарк':            '/images/categories/aquapark.jpg',
  'Антикафе':            '/images/categories/anti-cafe.jpg',
  'Океанариум':            '/images/categories/aquarium.jpg',
  'Дельфинарий':            '/images/categories/dolphinarium.jpg',
  'Музей':               '/images/categories/museum.jpg',
  'Бильярдный клуб':     '/images/categories/billiards.jpg',
  'Боулинг клуб':        '/images/categories/bowling.jpg',
  'Боулинг центр':        '/images/categories/bowling.jpg',
  'Зоопарк':             '/images/categories/zoo.jpg',
  'Кинотеатр':           '/images/categories/cinema.jpg',
  'Термальный комплекс': '/images/categories/thermal.jpg',
  'Театр':               '/images/categories/theather.jpg',
  'Котокафе':            '/images/categories/cat-cafe.jpg',
};

export function getPlaceImage(place) {
  // Если бэкенд когда-нибудь пришлёт image_url — используем его
  if (place.image_url) return place.image_url;

  // Иначе — картинка по типу места
  if (place.place_type && IMAGE_MAP[place.place_type]) {
    return IMAGE_MAP[place.place_type];
  }

  return null;
}