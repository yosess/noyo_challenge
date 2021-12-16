import logging

from datetime import date, datetime, timedelta

from flask import abort, jsonify
from webargs.flaskparser import use_args

from marshmallow import Schema, fields

from service.server import app, db
from service.models import AddressSegment
from service.models import Person


class GetAddressQueryArgsSchema(Schema):
    date = fields.Date(required=False, missing=datetime.utcnow().date())


class AddressSchema(Schema):
    class Meta:
        ordered = True

    street_one = fields.Str(required=True, max=128)
    street_two = fields.Str(max=128)
    city = fields.Str(required=True, max=128)
    state = fields.Str(required=True, max=2)
    zip_code = fields.Str(required=True, max=10)

    start_date = fields.Date(required=True)
    end_date = fields.Date(required=False)


@app.route("/api/persons/<uuid:person_id>/address", methods=["GET"])
@use_args(GetAddressQueryArgsSchema(), location="querystring")
def get_address(args, person_id):
    person = Person.query.get(person_id)
    if person is None:
        abort(404, description="person does not exist")
    elif len(person.address_segments) == 0:
        abort(404, description="person does not have an address, please create one")

    address_segment = person.address_segments[0]
    return jsonify(AddressSchema().dump(address_segment))


@app.route("/api/persons/<uuid:person_id>/address", methods=["PUT"])
@use_args(AddressSchema())
def create_address(payload, person_id):
    person = Person.query.get(person_id)
    if person is None:
        abort(404, description="person does not exist")
    # If there are AddressSegment records present for the person, we can check dates.
    elif len(person.address_segments) > 0:        

        # If the start_date provided is not greater than most recent
        # address segment start_date, raise an Exception.
        last_address = person.address_segments[0]
        if last_address.start_date > payload.get("start_date"):
            abort(404, description="The start date for this new segment must be greater than most recent address")
        else:
            # Seting end_date to the start date for new address
            last_address.end_date = payload.get("start_date")
            db.session.commit()
    # If there are no existing AddressSegments or new one is after more recent one, create a new AddressSegment
    # that begins on the start_date provided in the API request and continues into the future.  
        
    address_segment = AddressSegment(
        street_one=payload.get("street_one"),
        street_two=payload.get("street_two"),
        city=payload.get("city"),
        state=payload.get("state"),
        zip_code=payload.get("zip_code"),
        start_date=payload.get("start_date"),
        person_id=person_id,
    )

    db.session.add(address_segment)
    db.session.commit()
    db.session.refresh(address_segment)

    return jsonify(AddressSchema().dump(address_segment))
