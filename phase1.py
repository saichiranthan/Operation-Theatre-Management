import pandas as pd
import simpy
import random
import matplotlib.pyplot as plt

NUM_OPERATING_ROOMS = 2
SIMULATION_TIME = 480

urgency_levels = ['Normal', 'Emergency']
procedure_names = ['Appendectomy', 'Cholecystectomy', 'Hysterectomy', 'Laparoscopy', 'Prostatectomy']
available_equipment = ['Laparoscope', 'Endoscope', 'Microscope', 'Ultrasound']
surgeon_names = ['Dr. Smith', 'Dr. Johnson', 'Dr. Brown', 'Dr. Davis', 'Dr. Garcia']

class SurgicalProcedure:
    def __init__(self, procedure_id, urgency_level, procedure_name, equipment, surgeon, arrival_time, duration):
        self.procedure_id = procedure_id
        self.urgency_level = urgency_level
        self.procedure_name = procedure_name
        self.equipment = equipment
        self.surgeon = surgeon
        self.arrival_time = arrival_time
        self.duration = duration
        self.start_time = None
        self.end_time = None

def load_dataset(filename):
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        return []
    procedures = []
    for _, row in df.iterrows():
        procedure = SurgicalProcedure(row['id'], row['urgency_level'], row['procedure_name'],
                                      row['equipment'], row['surgeon'], row['arrival_time'], row['duration'])
        procedures.append(procedure)
    return procedures

def schedule_surgeries(env, procedures, room_resources, resource_allocation):
    emergency_procedures = [procedure for procedure in procedures if procedure.urgency_level == 'Emergency']
    elective_procedures = [procedure for procedure in procedures if procedure.urgency_level != 'Emergency']
    
    for procedure in emergency_procedures:
        room_id = random.randint(0, NUM_OPERATING_ROOMS - 1)
        env.process(surgery_process(env, procedure, room_resources, resource_allocation, room_id))
        
    for procedure in elective_procedures:
        room_id = random.randint(0, NUM_OPERATING_ROOMS - 1)
        env.process(surgery_process(env, procedure, room_resources, resource_allocation, room_id))

def surgery_process(env, procedure, room_resources, resource_allocation, room_id):
    yield env.timeout(procedure.arrival_time)
    procedure.start_time = env.now
    print(f"Starting {procedure.procedure_name} (ID: {procedure.procedure_id}) with urgency level {procedure.urgency_level} at time {env.now}")
    with room_resources.request(priority=1 if procedure.urgency_level == 'Emergency' else 0) as request:
        yield request
        # Update resource allocation for rooms
        resource_allocation['rooms'][f'Room {room_id+1}'].append((env.now, 1))  # Example: Increment room availability by 1
        yield env.timeout(procedure.duration)
    procedure.end_time = env.now
    print(f"Completed {procedure.procedure_name} (ID: {procedure.procedure_id}) at time {env.now}")

def save_procedures_to_csv(procedures):
    df = pd.DataFrame([vars(p) for p in procedures])
    df.to_csv("D:\\Btech_AI\\4thsem\\OS\\Project\\procedures.csv", index=False)

def create_procedures(num_procedures):
    procedures = []
    for i in range(num_procedures):
        procedure_id = i
        urgency_level = 'Emergency' if random.random() < 0.3 else 'Normal'  # 30% chance for Emergency
        procedure_name = random.choice(procedure_names)
        equipment = random.choice(available_equipment) if random.random() < 0.5 else None
        surgeon = random.choice(surgeon_names) if random.random() < 0.5 else None
        arrival_time = random.randint(0, 20)
        duration = random.uniform(1, 5)
        procedure = SurgicalProcedure(procedure_id, urgency_level, procedure_name, equipment, surgeon, arrival_time, duration)
        procedures.append(procedure)
    
    save_procedures_to_csv(procedures)
    return procedures

def plot_gantt_chart(procedures):
    fig, ax = plt.subplots(figsize=(10, len(procedures) * 0.5))
    for i, procedure in enumerate(procedures):
        if procedure.start_time is not None and procedure.end_time is not None:
            duration = procedure.end_time - procedure.start_time
            ax.barh(i, duration, left=procedure.start_time, color='blue', alpha=0.7, edgecolor='black')
            ax.text(procedure.start_time + 5, i, f"{procedure.procedure_name} (ID: {procedure.procedure_id})",
                    verticalalignment='center', fontsize=8)
            ax.text(procedure.start_time + 5, i + 0.2, f"Surgeon: {procedure.surgeon}",
                    verticalalignment='center', fontsize=6)
            ax.text(procedure.start_time + 5, i - 0.2, f"Urgency: {procedure.urgency_level}",
                    verticalalignment='center', fontsize=6)
    ax.set_xlabel('Time (minutes)')
    ax.set_ylabel('Procedures')
    ax.set_title('Surgical Procedures Gantt Chart')
    ax.set_yticks(range(len(procedures)))
    ax.set_yticklabels([f"{procedure.procedure_name} (ID: {procedure.procedure_id})" for procedure in procedures])
    ax.grid(True)
    plt.show()

def plot_charts(resource_allocation):
    fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(12, 18), sharex=True)

    # Plot resource allocation graph for rooms
    room_data = []
    for sub_resource_name, sub_allocation_data in resource_allocation['rooms'].items():
        if isinstance(sub_allocation_data, list):
            if sub_allocation_data:
                room_data.extend(sub_allocation_data)

    times, availability = zip(*room_data)
    axs[0].step(times, availability, where='post', label='Room Availability')

    axs[0].set_title('Room Allocation Over Time', fontsize=14)
    axs[0].set_ylabel('Number of Available Rooms', fontsize=12)
    axs[0].legend(fontsize=12, loc='upper right')
    axs[0].grid(True)
    axs[0].set_ylim(0, NUM_OPERATING_ROOMS)  # Set y-axis limits

    # Plot resource allocation graph for equipment
    for sub_resource_name, sub_allocation_data in resource_allocation['equipment'].items():
        if isinstance(sub_allocation_data, list):
            if sub_allocation_data:
                times = range(len(sub_allocation_data))
                axs[1].step(times, sub_allocation_data, where='post', label=sub_resource_name)

    axs[1].set_title('Equipment Allocation Over Time', fontsize=14)
    axs[1].set_ylabel('Number of Available Equipment', fontsize=12)
    axs[1].legend(fontsize=12, loc='upper right')
    axs[1].grid(True)
    axs[1].set_ylim(0, len(available_equipment))  # Set y-axis limits

    # Plot resource allocation graph for doctors
    for sub_resource_name, sub_allocation_data in resource_allocation['doctors'].items():
        if isinstance(sub_allocation_data, list):
            if sub_allocation_data:
                times = range(len(sub_allocation_data))
                axs[2].step(times, sub_allocation_data, where='post', label=sub_resource_name)

    axs[2].set_title('Doctor Allocation Over Time', fontsize=14)
    axs[2].set_ylabel('Number of Available Doctors', fontsize=12)
    axs[2].legend(fontsize=12, loc='upper right')
    axs[2].grid(True)
    axs[2].set_ylim(0, len(surgeon_names))  # Set y-axis limits

    plt.subplots_adjust(hspace=0.5)  # Increase vertical spacing between subplots

    # Set shared x-axis label and adjust tick label format
    fig.supxlabel('Time (minutes)', fontsize=14)
    for ax in axs:
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):03d}"))

    plt.tight_layout()
    plt.show()
def room_process(env, room_resources, resource_allocation, procedures, room_id):
    while True:
        yield env.timeout(1)
        procedures_in_room = [p for p in procedures if p.start_time is not None and p.end_time is not None and p.start_time <= env.now <= p.end_time]
        num_procedures_in_room = len(procedures_in_room)
        resource_allocation['rooms'][f'Room {room_id+1}'].append((env.now, NUM_OPERATING_ROOMS - num_procedures_in_room))

        # Update equipment allocation
        equipment_usage = {}
        for equip in available_equipment:
            procedures_using_equip = [p for p in procedures_in_room if p.equipment == equip]
            num_available = len([p for p in procedures if p.equipment != equip])
            resource_allocation['equipment'][equip].append(num_available)
            equipment_usage[equip] = procedures_using_equip

        # Update doctor allocation
        doctor_usage = {}
        for doctor in surgeon_names:
            procedures_with_doctor = [p for p in procedures_in_room if p.surgeon == doctor]
            num_available = len([p for p in procedures if p.surgeon != doctor])
            resource_allocation['doctors'][doctor].append(num_available)
            doctor_usage[doctor] = procedures_with_doctor

        # Handle resource conflicts
        for procedure in procedures_in_room:
            if procedure.equipment and procedure.equipment not in equipment_usage:
                print(f"Conflict: Procedure {procedure.procedure_id} requires {procedure.equipment}, but it's not available.")
            if procedure.surgeon and procedure.surgeon not in doctor_usage:
                print(f"Conflict: Procedure {procedure.procedure_id} requires {procedure.surgeon}, but they're not available.")

        # Update resource usage duration
        for equip, procedures_using_equip in equipment_usage.items():
            for proc in procedures_using_equip:
                if proc.start_time is not None and proc.end_time is None:
                    proc.end_time = env.now + proc.duration  # Set the end time based on the procedure duration

        for doctor, procedures_with_doctor in doctor_usage.items():
            for proc in procedures_with_doctor:
                if proc.start_time is not None and proc.end_time is None:
                    proc.end_time = env.now + proc.duration  # Set the end time based on the procedure duration
def main():
    num_procedures = int(input("Enter number of procedures: "))
    procedures = create_procedures(num_procedures)
    env = simpy.Environment()
    room_resources = simpy.PriorityResource(env, capacity=NUM_OPERATING_ROOMS)
    resource_allocation = {'rooms': {f'Room {i+1}':[] for i in range(NUM_OPERATING_ROOMS)},
                           'equipment': {equip: [] for equip in available_equipment},
                           'doctors': {doctor: [] for doctor in surgeon_names}}

    for i in range(NUM_OPERATING_ROOMS):
        env.process(room_process(env, room_resources, resource_allocation, procedures, i))

    schedule_surgeries(env, procedures, room_resources, resource_allocation)
    env.run(until=SIMULATION_TIME)

    plot_gantt_chart(procedures)
    plot_charts(resource_allocation)

if __name__ == "__main__":
    main()

