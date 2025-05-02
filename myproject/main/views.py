from django.conf import settings

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from rest_framework import generics
from .models import Review

from .models import Restaurant, Table, Reservation, Review
from .forms import ReservationForm, CustomUserCreationForm, ReviewForm
from .serializers import RestaurantSerializer, ReservationSerializer

from .permissions import IsAuthenticated401

import re




def account_dashboard(request):
    # При заходе сразу перенаправляем на «Мои брони»
    return redirect('account_bookings')



@login_required
def account_bookings(request):
    today    = timezone.localdate()
    upcoming = Reservation.objects.filter(
                   user=request.user,
                   date__gte=today
               ).order_by('date','time')
    past     = Reservation.objects.filter(
                   user=request.user,
                   date__lt =today
               ).order_by('-date','-time')
    return render(request, 'account/bookings.html', {
        'upcoming': upcoming,
        'past':     past,
    })
@login_required
def account_reviews(request):
    my_reviews = Review.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'account/reviews.html', {
        'reviews': my_reviews,
    })
@login_required
def account_profile(request):
    # просто показываем request.user.username и email,
    # тут же можно будет добавить форму редактирования
    return render(request, 'account/profile.html', {
        'user': request.user,
    })

@login_required
def account_settings(request):
    # сюда будем выводить формы уведомлений, смены пароля и т.п.
    return render(request, 'account/settings.html', {})




@login_required
def account_favorites(request):
    # предполагаем, что в модели Restaurant есть M2M-поле `favorited_by`
    favorites = request.user.favorite_restaurants.all()
    return render(request, 'account/favorites.html', {
        'favorites': favorites,
    })


def home(request):
    return render(request, 'main/index.html')


def about(request):
    return render(request, 'main/about.html')


def restaurant_list(request):
    qs = Restaurant.objects.exclude(lat__isnull=True, lon__isnull=True).order_by('name')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(address__icontains=q))

    paginator = Paginator(qs, 9)
    page = request.GET.get('page', 1)
    try:
        restaurants = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        restaurants = paginator.page(1)

    return render(request, 'main/restaurant_list.html', {
        'restaurants': restaurants,
        'search_query': q,
        'dgis_api_key': settings.DGIS_API_KEY,
        'yandex_maps_key': settings.YANDEX_MAPS_API_KEY,
    })

from datetime import datetime, date, time, timedelta
from django.utils import timezone

from .models import Restaurant, Reservation
from .forms import ReservationForm

from datetime import datetime, date, time, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Restaurant, Reservation
from .forms import ReservationForm






@login_required
def make_reservation(request):
    rest_id = request.GET.get('restaurant') or request.POST.get('restaurant')
    if not rest_id:
        messages.warning(request, "Сначала выберите ресторан.")
        return redirect('restaurant_list')

    restaurant = get_object_or_404(Restaurant, pk=rest_id)

    hours_text = restaurant.hours or ""
    m = re.search(r'(\d{1,2}:\d{2})[–-](\d{1,2}:\d{2})', hours_text)
    if m:
        start_str, end_str = m.group(1), m.group(2)
        if end_str == '24:00':
            end_str = '23:59'
        work_start = datetime.strptime(start_str, '%H:%M').time()
        work_end = datetime.strptime(end_str, '%H:%M').time()
    else:
        work_start, work_end = time(10, 0), time(22, 0)

    today = date.today()
    max_date = today + timedelta(days=30)
    date_options = [today + timedelta(days=i) for i in range(7)]
    selected_date_str = request.POST.get('date') or request.GET.get('date')
    selected_date = None

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    if selected_date == today:
        now = datetime.now()
        mins = ((now.minute + 14) // 15) * 15
        h, m = now.hour + mins // 60, mins % 60
        rounded = time(h % 24, m)
        min_time = max(rounded, work_start)
    else:
        min_time = work_start
    force_update = True
    end_limit = (datetime.combine(selected_date, work_end) - timedelta(hours=2)).time()
    max_time = end_limit

    slots = []
    dt_cursor = datetime.combine(selected_date, min_time)
    dt_end    = datetime.combine(selected_date, max_time)
    while dt_cursor <= dt_end:
        slots.append(dt_cursor.time().strftime('%H:%M'))
        dt_cursor += timedelta(minutes=15)

    if request.method == 'POST':
        form = ReservationForm(request.POST, restaurant_id=rest_id)
        if form.is_valid():
            r = form.save(commit=False)
            r.user = request.user
            r.end_time = (datetime.combine(r.date, r.time) + timedelta(hours=2)).time()

            taken_ids = Reservation.objects.filter(
                date=r.date, time=r.time, table__restaurant=restaurant
            ).values_list('table_id', flat=True)
            free = restaurant.tables.exclude(id__in=taken_ids).first()
            if not free:
                messages.error(request, "Извините, свободных столов нет на это время.")
                return redirect(f'/reserve/?restaurant={restaurant.pk}')

            r.table = free
            r.save()
            messages.success(request, "\U0001F389 Бронь создана успешно!")
            return redirect('my_reservations')
        else:
            messages.error(request, "Проверьте данные формы.")
    else:
        form = ReservationForm(restaurant_id=rest_id)

    guests_options = list(range(1, 7))
    return render(request, 'main/reservation_form.html', {
        'restaurant': restaurant,
        'form': form,
        'guests_options': guests_options,
        'date_options': date_options,
        'time_slots': slots,
        'work_start': work_start.strftime('%H:%M'),
        'work_end': work_end.strftime('%H:%M'),
        'today_iso': today.isoformat(),
        'max_date_iso': max_date.isoformat(),
    })







def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "✅ Регистрация прошла успешно!")
            return redirect('home')
        else:
            messages.error(request, "Проверьте данные регистрации.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'main/register.html', {'form': form})


def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    print("Координаты:", restaurant.lat, restaurant.lon)

    # свободные столы на сегодня
    today = timezone.localdate()
    reserved = Reservation.objects.filter(
        date=today, table__restaurant=restaurant
    ).values_list('table_id', flat=True)
    available_tables = restaurant.tables.exclude(id__in=reserved)

    # последние 3 отзыва
    reviews = restaurant.reviews.order_by('-created_at')[:3]

    # форма отзыва
    form = ReviewForm(request.POST or None)
    if request.method=='POST' and 'review_submit' in request.POST:
        if not request.user.is_authenticated:
            messages.error(request, "Нужно войти, чтобы оставить отзыв.")
            return redirect('login')
        if form.is_valid():
            rev = form.save(commit=False)
            rev.user = request.user
            rev.restaurant = restaurant
            rev.save()
            messages.success(request, "Спасибо за отзыв!")
            return redirect('restaurant_detail', pk=pk)
        else:
            messages.error(request, "Проверьте форму отзыва.")

    return render(request, 'main/restaurant_detail.html', {
        'restaurant': restaurant,
        'today': today,
        'available_tables': available_tables,
        'reviews': reviews,
        'form': form,
        'yandex_maps_key': settings.YANDEX_MAPS_API_KEY,
    })

@login_required
def profile(request):
    user = request.user
    upcoming = user.reservations.filter(date__gte=date.today()).order_by('date','time')
    past     = user.reservations.filter(date__lt =date.today()).order_by('-date','-time')
    my_reviews = Review.objects.filter(user=user).order_by('-created_at')
    return render(request, 'main/profile.html', {
        'upcoming': upcoming,
        'past':     past,
        'my_reviews': my_reviews,

    })

from django.shortcuts import redirect

@login_required
def toggle_favorite(request, pk):
    rest = get_object_or_404(Restaurant, pk=pk)
    if request.user in rest.favorited_by.all():
        rest.favorited_by.remove(request.user)
    else:
        rest.favorited_by.add(request.user)
    return redirect(request.META.get('HTTP_REFERER','restaurant_detail'))


@login_required
def my_reservations(request):
    res = Reservation.objects.filter(user=request.user).order_by('-date','-time')
    return render(request, 'main/my_reservations.html', {'reservations':res})


@login_required
def cancel_reservation(request, pk):
    r = get_object_or_404(Reservation, pk=pk, user=request.user)
    if request.method=='POST':
        r.delete()
        messages.success(request, "✅ Бронь отменена.")
    return redirect('my_reservations')


# ——— API ——————————————————————————————

class RestaurantListAPI(generics.ListAPIView):
    serializer_class = RestaurantSerializer

    def get_queryset(self):
        q = self.request.GET.get('q', '')
        qs = Restaurant.objects.all()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(address__icontains=q))
        return qs
class ReservationDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated401]

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)


class ReservationListCreateAPI(generics.ListCreateAPIView):
    serializer_class   = ReservationSerializer
    permission_classes = [IsAuthenticated401]
    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import ProfileForm, UserEmailForm, CustomPasswordChangeForm

@login_required
def profile_settings(request):
    profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
    email_form   = UserEmailForm(request.POST or None, initial={'email': request.user.email})
    pwd_form     = CustomPasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == 'POST':
        if 'save_profile' in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Аватар обновлён.")
            return redirect('profile_settings')

        if 'save_email' in request.POST and email_form.is_valid():
            request.user.email = email_form.cleaned_data['email']
            request.user.save()
            messages.success(request, "Email обновлён.")
            return redirect('profile_settings')

        if 'change_password' in request.POST and pwd_form.is_valid():
            user = pwd_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Пароль изменён.")
            return redirect('profile_settings')

    return render(request, 'main/profile_settings.html', {
        'profile_form': profile_form,
        'email_form':   email_form,
        'pwd_form':     pwd_form,
    })
from django.http import JsonResponse
from django.utils import timezone

def available_tables_api(request):
    """
    Возвращает JSON-список свободных столов для ресторана на дату+время.
    GET-параметры:
      - restaurant (ID ресторана)
      - date (YYYY-MM-DD)
      - time (HH:MM)
    """
    rest_id = request.GET.get('restaurant')
    date = request.GET.get('date')
    time = request.GET.get('time')
    if not (rest_id and date and time):
        return JsonResponse({'error': 'Не указан restaurant/date/time'}, status=400)

    # получаем ресторан и занятые столы
    from .models import Restaurant, Reservation
    restaurant = get_object_or_404(Restaurant, pk=rest_id)
    reserved = Reservation.objects.filter(date=date, time=time, table__restaurant=restaurant) \
                                  .values_list('table_id', flat=True)
    tables = restaurant.tables.exclude(id__in=reserved) \
                  .values('id', 'number', 'seats')
    return JsonResponse(list(tables), safe=False)


from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .views_external import external_restaurants
from .models import Restaurant, Table

@require_POST
def update_restaurants(request):
    count = 0
    external = external_restaurants(limit=50)
    for ext in external:
        obj, created = Restaurant.objects.update_or_create(
            name=ext['name'],
            defaults={
                'address': ext['address'],
                'address_comment': ext['address_comment'],
                'phone': ext['phone'],
                'hours': ext['hours'],
                'website': ext['website'],
                'rating': ext['rating'],
                'purpose_name': ext['purpose_name'],
                'type': ext['type'],
                'is_24x7': ext['is_24x7'],
                'avatar_url': ext['avatar_url'],
                'lat': ext['lat'],
                'lon': ext['lon'],
            }
        )
        if created:
            for i in range(1, 11):
                Table.objects.create(restaurant=obj, number=i, seats=4)
        count += 1

    return JsonResponse({'message': f'Обновлено ресторанов: {count}'})


from django.http import HttpResponse
from django.template.loader import render_to_string

def search_suggestions(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        results = Restaurant.objects.filter(
            Q(name__icontains=q) |
            Q(address__icontains=q) |
            Q(phone__icontains=q)
        )[:5]

    html = render_to_string('main/_search_suggestions.html', {'results': results})
    return HttpResponse(html)

