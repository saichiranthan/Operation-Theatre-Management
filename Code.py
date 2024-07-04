import pandas as pd
import random
import matplotlib.pyplot as plt
from collections import defaultdict

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
        self.remaining_time = duration

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

def save_procedures_to_csv(procedures):
    df = pd.DataFrame([vars(p) for p in procedures])
    df.to_csv("procedures.csv", index=False)

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
                times, availability = zip(*sub_allocation_data)
                axs[1].step(times, availability, where='post', label=sub_resource_name)

    axs[1].set_title('Equipment Allocation Over Time', fontsize=14)
    axs[1].set_ylabel('Number of Available Equipment', fontsize=12)
    axs[1].legend(fontsize=12, loc='upper right')
    axs[1].grid(True)
    axs[1].set_ylim(0, len(available_equipment))  # Set y-axis limits

    # Plot resource allocation graph for doctors
    for sub_resource_name, sub_allocation_data in resource_allocation['doctors'].items():
        if isinstance(sub_allocation_data, list):
            if sub_allocation_data:
                times, availability = zip(*sub_allocation_data)
                axs[2].step(times, availability, where='post', label=sub_resource_name)

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

def priority_scheduling_no_deadlocks(procedures):
    available_equipment_dict = {equip: 1 for equip in available_equipment}
    available_surgeons = {doctor: 1 for doctor in surgeon_names}

    max_resources = defaultdict(list)
    allocated_resources = defaultdict(list)

    for i, procedure in enumerate(procedures):
        max_resources[i] = [1, available_equipment_dict[procedure.equipment] if procedure.equipment else 0, 1 if procedure.surgeon else 0]
        allocated_resources[i] = [0] * len(max_resources[i])

    current_time = 0
    safe_sequence = banker_algorithm([NUM_OPERATING_ROOMS] + list(available_equipment_dict.values()) + list(available_surgeons.values()),
                                    list(max_resources.values()),
                                    list(allocated_resources.values()))

    if safe_sequence is None:
        print("Deadlock detected! Using alternative priority scheduling...")
        procedures.sort(key=lambda p: (p.urgency_level == 'Emergency', p.arrival_time), reverse=True)
        
        scheduled_procedures = [proc for proc in procedures
                                if not (proc.surgeon and
                                        max_resources[proc.procedure_id][2] == allocated_resources[proc.procedure_id][2] and
                                        all(allo_resource[1] > 0 for allo_resource in allocated_resources.values()
                                            if (allo_resource[1] > 0) and (allo_resource[0] == proc.procedure_id)))]
        scheduled_procedures.sort(key=lambda p: p.arrival_time)

        for procedure in scheduled_procedures:
            if procedure.start_time is None:
                procedure.start_time = current_time
                print(f"Starting {procedure.procedure_name} (ID: {procedure.procedure_id}) with urgency level {procedure.urgency_level} at time {current_time}")

                allocate_resources(procedure, allocated_resources)

                current_time += procedure.duration

                procedure.end_time = current_time
                print(f"Completed {procedure.procedure_name} (ID: {procedure.procedure_id}) at time {current_time}")

                deallocate_resources(procedure, allocated_resources)

        plot_gantt_chart(scheduled_procedures)

    else:
        priority_scheduling_banker(procedures, allocated_resources, safe_sequence, current_time)

def allocate_resources(procedure, allocated_resources):
    available_equipment_dict[procedure.equipment] -= 1
    allocated_resources[procedure.procedure_id][1] = 1
    
    if procedure.surgeon:
        available_surgeons[procedure.surgeon] -= 1
        allocated_resources[procedure.procedure_id][2] = 1

def deallocate_resources(procedure, allocated_resources):
    available_equipment_dict[procedure.equipment] += 1
    allocated_resources[procedure.procedure_id][1] = 0

    if procedure.surgeon:
        available_surgeons[procedure.surgeon] += 1
        allocated_resources[procedure.procedure_id][2] = 0

def priority_scheduling_banker(procedures, allocated_resources, safe_sequence, current_time):
    for i in safe_sequence:
        procedure = procedures[i]

        if procedure.start_time is None:
            procedure.start_time = current_time
            print(f"Starting {procedure.procedure_name} (ID: {procedure.procedure_id}) with urgency level {procedure.urgency_level} at time {current_time}")

            allocate_resources(procedure, allocated_resources)

            current_time += procedure.duration

            procedure.end_time = current_time
            print(f"Completed {procedure.procedure_name} (ID: {procedure.procedure_id}) at time {current_time}")

            deallocate_resources(procedure, allocated_resources)
if __name__ == "__main__":
    num_procedures = int(input("Enter number of procedures: "))
    procedures = create_procedures(num_procedures)
    priority_scheduling_no_deadlocks(procedures)