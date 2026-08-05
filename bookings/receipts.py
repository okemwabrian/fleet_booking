from django.template.loader import render_to_string
from weasyprint import HTML


def build_booking_receipt_pdf(booking, request=None):
    html = render_to_string(
        'receipts/booking_receipt.html',
        {
            'booking': booking,
        },
        request=request,
    )
    base_url = request.build_absolute_uri('/') if request else None
    return HTML(string=html, base_url=base_url).write_pdf()