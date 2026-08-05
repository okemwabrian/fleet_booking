from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from bookings.models import Booking, ParcelShipment
from profiles.models import UserProfile
from routes.models import Route
from vehicles.models import Vehicle


class StyledFormMixin:
    def _apply_field_classes(self):
        base_classes = 'mt-2 w-full rounded-2xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-slate-100 placeholder-slate-500 shadow-sm outline-none transition focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30'
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} {base_classes}'.strip()


class CustomerSignUpForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False, max_length=150)
    last_name = forms.CharField(required=False, max_length=150)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_classes()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user


class RouteSearchForm(StyledFormMixin, forms.Form):
    origin = forms.CharField(required=True, max_length=150)
    destination = forms.CharField(required=True, max_length=150)
    travel_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_classes()


class CustomerLoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_classes()


class ProfileUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar', 'phone_number', 'theme_preference')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_classes()


class AdminBookingForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Booking
        fields = (
            'customer',
            'route',
            'vehicle',
            'travel_date',
            'seats_booked',
            'contact_phone',
            'contact_email',
            'status',
            'total_price',
            'payment_proof',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_classes()
        self.fields['total_price'].required = False

    def save(self, commit=True):
        booking = super().save(commit=False)
        if not booking.total_price and booking.route_id:
            booking.total_price = booking.route.base_price * booking.seats_booked
        if commit:
            booking.save()
        return booking


class AdminVehicleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ('make', 'model', 'year', 'license_plate', 'capacity', 'status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_classes()


class AdminRouteForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Route
        fields = ('origin', 'destination', 'distance_km', 'base_price', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_classes()


class ParcelCreateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ParcelShipment
        fields = (
            'route',
            'sender_name',
            'sender_phone',
            'sender_email',
            'receiver_name',
            'receiver_phone',
            'receiver_email',
            'parcel_description',
            'weight_kg',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_classes()


class AdminParcelForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ParcelShipment
        fields = (
            'customer',
            'route',
            'tracking_code',
            'sender_name',
            'sender_phone',
            'sender_email',
            'receiver_name',
            'receiver_phone',
            'receiver_email',
            'parcel_description',
            'weight_kg',
            'fee',
            'status',
            'current_location',
            'expected_delivery_date',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_field_classes()
        self.fields['tracking_code'].required = False
        self.fields['customer'].required = False