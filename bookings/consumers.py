from channels.generic.websocket import AsyncJsonWebsocketConsumer


class BookingDispatcherConsumer(AsyncJsonWebsocketConsumer):
    group_name = 'dispatcher'

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def booking_created(self, event):
        await self.send_json(
            {
                'type': 'booking.created',
                'booking': event['booking'],
            }
        )

    async def booking_updated(self, event):
        await self.send_json(
            {
                'type': 'booking.updated',
                'booking': event['booking'],
            }
        )

    async def parcel_created(self, event):
        await self.send_json(
            {
                'type': 'parcel.created',
                'parcel': event['parcel'],
            }
        )

    async def parcel_updated(self, event):
        await self.send_json(
            {
                'type': 'parcel.updated',
                'parcel': event['parcel'],
            }
        )